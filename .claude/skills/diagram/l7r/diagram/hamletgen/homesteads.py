"""STAGE 5-6: the houses on their lane frontage, their appurtenances, and the wells.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence
from typing import Any

from l7r.diagram.settlement import Settlement, point_in_poly, seg_dist, surface_water_dist
from l7r.diagram.sitegen.geom import centroid, unit

from .consts import BUNDLE_PITCH, CLUSTER_DRAWN_ASPECT, CLUSTER_ROW_SPAN, CLUSTER_SPAN_FACTOR, LANE_FRONTAGE_STANDOFF, SUN_CORRIDOR_FT, Pt
from .plan import SitePlan

# ---- STAGE 5: the homesteads --------------------------------------------------------------------


def front_row(plan: SitePlan, count: int, standoff: float = 46.0) -> list[Pt]:
    """Seats for the row of homesteads that FRONTS the field, offset from the field OUTLINE itself.

    Offsetting from the cluster band's straight near face is not the same thing and is not good
    enough: the outline curves away from the band, so a row laid along the face can sit 32 px from
    the field at its middle and 300 px from it at its ends, and `field_ringed` (five farmhouses
    within 165 px of the outline) then fails on a map whose cluster is plainly beside its paddy.
    Following the outline also draws better - a farming hamlet's front row bends with the field edge
    the way a real one does, rather than ruling a straight line across a curved margin."""
    env = plan.envelope
    cen = centroid(env)
    seat = plan.seat
    ax, ay = seat["along"]
    # the stretch of outline this cluster fronts: everything within the band's lateral reach
    # The row spans 1.6x the band's own length along the outline. Confined to `lat` exactly, all its
    # candidates come off one short arc - and if that arc happens to be blocked (crop up to the bund,
    # a delivery ditch's corridor, the field spur), the whole row is refused together and the field
    # ends up ringed by four houses instead of five. Wrapping further round the field costs nothing:
    # a seat too far along is dropped by the caller's own band test.
    # The rolled shape governs how far the row wraps - see `CLUSTER_ROW_SPAN`. Without it the band
    # aspect alone left an "elongated" map drawing 1.2:1, i.e. a declared knob that did not
    # describe the sheet.
    _rowspan = CLUSTER_ROW_SPAN.get(plan.cluster_shape or "crescent", CLUSTER_SPAN_FACTOR)
    span = [(i, p) for i, p in enumerate(env) if abs((p[0] - seat["anchor"][0]) * ax + (p[1] - seat["anchor"][1]) * ay) <= seat["lat"] * _rowspan]
    if len(span) < 2:  # pragma: no cover - a band always spans several outline vertices
        return []
    span.sort(key=lambda ip: (ip[1][0] - seat["anchor"][0]) * ax + (ip[1][1] - seat["anchor"][1]) * ay)
    # SAMPLE BY DENSITY, NOT BY HOUSEHOLD COUNT (2026-08-17). `count` is what the caller still WANTS
    # seated, but using it to space the candidates too made the row's resolution depend on the size
    # of the village rather than on the length of the field edge it fronts - so a 10-household
    # hamlet beside a 28-acre paddy got ten seats spread over a very long outline, several hundred
    # px apart. The near margin is the busiest ground on the map (crop up to the bund, delivery
    # ditches and their corridors, the field spur), so a coarse row loses most of its candidates to
    # blocked ground and leaves the field ringed by three houses instead of five - which is cohort
    # seed 22, where the front row placed 5 of 32 offers and only 3 finished inside `field_ringed`'s
    # 165 px band.
    #
    # THE HONEST SPACING IS ONE BUNDLE PITCH: two homesteads cannot stand closer than that, so
    # sampling finer wastes offers, and sampling coarser leaves gaps a blocked seat cannot recover
    # from. Offering more costs nothing - a seat too far along is dropped by the caller's own band
    # test, and the loop stops as soon as the households are seated. Measured across the cohort:
    # seed 22 goes 3 -> 10 farmhouses within the band (and its gate clean), seed 1 goes 11 -> 15,
    # seed 4 goes 15 -> 16, and no map loses ground. It is also how a farming hamlet really sits -
    # the houses crowd the field they work.
    _span_len = sum(math.dist(span[i][1], span[i + 1][1]) for i in range(len(span) - 1))
    count = max(count, min(int(_span_len / BUNDLE_PITCH) + 1, 64))  # capped so a huge fan cannot make the row unbounded
    out: list[Pt] = []
    for k in range(count):
        idx = span[min(len(span) - 1, round(k * (len(span) - 1) / max(1, count - 1)))][0]
        a, b = env[idx], env[(idx + 1) % len(env)]
        nx, ny = unit(-(b[1] - a[1]), b[0] - a[0])
        if nx * (a[0] - cen[0]) + ny * (a[1] - cen[1]) < 0:
            nx, ny = -nx, -ny
        out.append((a[0] + nx * standoff, a[1] + ny * standoff))
    # ORDER CENTER-OUT, so the row FILLS rather than SPREADS (settlement-review on Inashiro,
    # 2026-08-17). Sampling by density fixed the starved row, but it also handed the placer a dense
    # line of seats along the WHOLE reachable margin in span order, and the caller takes them until
    # the households run out - so the row walked from one end of the arc to the other and the
    # cluster stretched with it. Measured cost on Inashiro: width 569 -> 445 ft at unchanged length,
    # elongation 3.79 -> 5.42 against 1.22 for the authored Ikegami on the identical brief, and two
    # more households pushed past the end of the lane skeleton.
    #
    # Offering the same seats in a different ORDER fixes it without giving the density back: the
    # busiest ground is the middle of the band, the row fills there first, and the `placed >=
    # households` break stops it before it reaches the far ends - which is exactly what
    # `lane_frontage` already does ("ordered from the cluster's center outward, so the lanes fill
    # from their busy end"), and a nucleated hamlet grows the same way, outward from its middle.
    return sorted(out, key=lambda q: math.hypot(q[0] - seat["cx"], q[1] - seat["cy"]))


_WELL_DRAWN_R = 12.0
"""The wellhead's DRAWN half-extent, used when asking how far a candidate seat would push the crop.
It is the `vr` the glyph draws (not the `r` clearance radius), because the frame follows the ink -
`crop_not_held_open_by_one_feature` quotes a well's extent as 16 px across."""

_FIELD_RING_FLOOR = 5
"""How many front-row seats are taken before `_FRONT_ROW_LANE_CAP` starts applying. It is
`field_ringed`'s own floor - five farmhouses within 165 px of the field outline - because that is a
GATE check while lane frontage is a form rule with none, so the cap must never be the reason a map
ships with four."""

_FRONT_ROW_LANE_CAP = 150.0
"""How far a FRONT-ROW seat may stand from a drawn lane before the row is offered it only as a
fallback. `field_ringed`'s own band is 165 px; a seat inside 150 of a track and 165 of the field
outline is both fronted and on its paddy, which is what the front row is for. See the ladder in
`stage_homesteads` for the defect this cures and why it relaxes rather than filters."""


def _lane_dist(s: Settlement, x: float, y: float) -> float:
    """Distance from a point to the nearest drawn lane centerline (inf when the map draws none).

    The CONNECTOR counts: it is the track the hamlet's traffic actually leaves by, and a farmstead
    fronting it is fronting a way. Reads `M["lanes"]`, which is what the map draws and what the
    frontage pass and `place_kosatsuba` both measure against - one source, per the same-source
    doctrine."""
    best = math.inf
    for lane in s.M.get("lanes", []):
        pts = lane.get("pts") or []
        for i in range(len(pts) - 1):
            best = min(best, seg_dist(x, y, pts[i], pts[i + 1]))
    return best


def lane_frontage(s: Settlement, seat: Mapping[str, Any], step: float = 86.0) -> list[Pt]:
    """Candidate seats along BOTH verges of every internal lane, just outside its no-build corridor.

    Ordered from the cluster's center outward, so the lanes fill from their busy end. The connector
    is skipped: it is the track OUT of the settlement, and lining it with farmhouses would string the
    hamlet along the road instead of nucleating it (that is the `linear` settlement form, a
    different archetype)."""
    out: list[Pt] = []
    off = LANE_FRONTAGE_STANDOFF
    for lane in s.M.get("lanes", []):
        if lane.get("connector") or lane.get("web"):
            continue
        pts = lane["pts"]
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            run = math.hypot(x1 - x0, y1 - y0)
            nx, ny = unit(-(y1 - y0), x1 - x0)
            k = 1
            while k * step < run:
                px, py = x0 + (x1 - x0) * (k * step / run), y0 + (y1 - y0) * (k * step / run)
                out += [(px + nx * off, py + ny * off), (px - nx * off, py - ny * off)]
                k += 1
    return sorted(out, key=lambda q: math.hypot(q[0] - seat["cx"], q[1] - seat["cy"]))


def stage_homesteads(s: Settlement, plan: SitePlan) -> None:
    """Seat every declared household, and KNOW whether it worked.

    `households_consistent` wants the occupied farmhouses within 0.85-1.05x the declared households -
    a to-scale map depicts essentially every household - so a hamlet that declares 15 and seats 12
    fails, and the authored maps deal with that by tuning a hand-written candidate loop until the
    number comes out. The script instead asks the placer, which is the only thing that actually knows
    whether a seat is free: it draws candidates from the rolled cluster shape and, if the quota is
    still short, GROWS the band and draws more, up to a cap.

    Growing rather than re-rolling is deliberate. A retry with a different seed would re-roll the
    whole map to fix a local shortfall - the expensive, whack-a-mole loop the skill's dev notes warn
    about. Widening the band changes only the ground the candidates come from, so the houses already
    seated stay exactly where they are and the map converges instead of churning."""
    # A YARD KEEPS ITS SUN (GM 2026-08-13; researched in research/homesteads.md, "The threshing
    # yard's sun"). 39 ft is the 9-to-3 drying window at 38N in the 10th month for a minka's ~20 ft
    # ridge; the noon figure is 21. The engine's rule is opt-in and this is where the scripted tier
    # opts in - the hand-authored maps keep their packing until they are converted.
    s.sun_corridor(SUN_CORRIDOR_FT)
    seat = plan.seat
    ax, ay = seat["along"]
    ox, oy = seat["out"]
    rng = random.Random((plan.spec.seed * 2654435761) & 0xFFFFFFFF)
    placed = 0
    lat, dep = seat["lat"], seat["dep"]

    # THE FRONT ROW GOES DOWN FIRST, along the band's field-facing face. A cluster seeded only by
    # its SHAPE fills its whole depth evenly, and on a small hamlet that can leave the field ringed
    # by four houses where `field_ringed` wants five - the map then reads as a settlement that
    # happens to be near a paddy rather than one that works it. Seating a row against the margin
    # first is also just what a farming hamlet looks like: the houses front the field they farm, and
    # the back rows fill in behind them.
    # (no quota guard here: the row is capped at 8 seats and the tier's floor is 10 households, so
    # the front row alone can never meet the ask)
    # TWO passes at two standoffs. `field_ringed` wants five farmhouses within 165 px of the field
    # outline, and a single row of eight candidates at one standoff can land four when the near
    # ground is awkward - the placer refuses a bundle that laps a bund or a ditch, and every refusal
    # is a house that ends up in the back rows instead. Offering the same row again a little further
    # out costs nothing when the first pass filled it and rescues the ring when it did not.
    # EVERY SEAT MUST LIE IN THE BAND. The front row follows the field OUTLINE and the frontage rows
    # follow the lanes, and both can wander well past the cluster on a long fan - which produced a
    # nucleated hamlet with three or four farmsteads strung hundreds of px down the margin. That is
    # a form defect on its own (a nucleus is supposed to read as a nucleus), and it was ALSO the
    # cause of three separate gate failures: a windbreak sized off the furthest house became a green
    # blanket, a copse over the full house bbox left the map no blank ground, and a stray farm past
    # the last well tripped `settlement_dwellings_watered`. Fixing the seats fixes all of it at the
    # source, which is why the percentile guards elsewhere are belt-and-braces rather than the cure.
    bound = 1.15 * math.hypot(lat, dep)

    def in_band(q: Pt) -> bool:
        return math.hypot(q[0] - seat["cx"], q[1] - seat["cy"]) <= bound

    # THREE standoffs, not two. `field_ringed` wants five farmhouses within 165 px of the field
    # outline and the placer refuses any bundle that laps a bund or a ditch, so a single ring of
    # candidates can land four on awkward ground. Each extra pass is free when the earlier one
    # filled the row.
    # The FRONT ROW is allowed a little further out than the rest - a house hugging the field is
    # part of the settlement wherever the band's nominal circle happens to fall, and `field_ringed`
    # wants five of them within 165 px of the outline.
    # Standoffs run out to 150 px, which is still inside `field_ringed`'s 165 px band. The near
    # ground is often the busiest on the map - crop up to the bund, the collector's out-of-crop
    # stretches with their corridors, the field spur - so a row that stops at 92 px can land four
    # houses where five are wanted while perfectly good ground sits at 120. A farmhouse 150 px from
    # its paddy is still a farmhouse on its paddy.
    # THE FRONT ROW IS ONE RANK, NOT THE WHOLE HAMLET (settlement-review on Inashiro and Mizuguchi,
    # 2026-08-17). Once the row began sampling by density it could seat every household by itself,
    # and it did: the cluster came out a single file along the paddy margin - Mizuguchi 891 x 123 ft,
    # aspect 7.24, with an rms residual of 22 ft about a smooth curve, so NO house stood behind any
    # other anywhere on the map. Inashiro went the same way (elongation 3.79 -> 5.42, width 569 ->
    # 445 ft at unchanged length) against 1.22 for the authored Ikegami on the identical brief. It
    # took the courtyards with it: Mizuguchi's copse collapsed 11 -> 4 clumps and its byres were
    # pushed 20+ ft out of the homestead courtyards into the windbreak, because a one-rank cluster
    # has no interior gap ground left. `consts.py` says the pitch is chosen to keep the cluster
    # "dense enough to read as a nucleus and open enough for its courtyards, its wells and its
    # byres"; a single rank has neither half.
    #
    # THE CAP IS ONE RANK'S WORTH OF THE BAND, derived rather than picked: the margin band is `lat`
    # long, and homesteads in it stand a bundle pitch apart, so `2 * lat / pitch` is how many fit in
    # the rank that fronts the field. Everything past that is a household the flanking and cloud
    # passes should seat BEHIND, which is what makes a nucleus a nucleus. Floored at 6 so
    # `field_ringed` (five farmhouses within 165 px of a big field's outline) can always be met by
    # the row alone - the defect this row exists to prevent.
    front_cap = min(plan.spec.households, max(6, int(2 * lat / BUNDLE_PITCH)))
    # ...AND A FRONT-ROW SEAT MUST ALSO BE REACHABLE FROM A TRACK, not merely near the paddy
    # (settlement-review, Inashiro 2026-08-17 - the same review round as the rank cap above, which
    # is the OTHER half of this defect: that one bounds HOW MANY seats the row takes, this one bounds
    # WHICH). The row runs FIRST and follows the field OUTLINE, which on a long fan strings it
    # hundreds of px past wherever the rolled lane skeleton lies - so the row won every seat and the
    # frontage pass below got the leftovers. Measured on Inashiro: house-to-lane median 109 ft, five
    # houses past 150, a whole seven-farmstead lobe fronting nothing, and a 252 ft lane spur with no
    # house within 96 ft anywhere. That is the defect the frontage pass's own comment below records
    # curing ("a median house-to-lane distance of 94 ft ... with one lane dead-ending in open
    # ground"), returned by a different route - and no gate check can see it, because `field_ringed`
    # is satisfied by exactly the seats that cause it.
    #
    # A CAP, NOT A LADDER - the difference was MEASURED, because the ladder is the shape every other
    # rung in this function uses and here it did nothing. Offering the whole standoff ladder twice,
    # once capped and once admitting anything, left every median where it started (109/59/65/118 ft):
    # the capped pass cannot fill the row on a long fan, so the uncapped pass seated the very houses
    # the cap had just refused. A cap only bites when there is no second chance at the same seats -
    # and none is needed, because the passes BELOW this one (lane frontage, the in-band cloud, four
    # widening rounds) are the real fallback and seat in-band ground by construction.
    #
    # TIGHTENING THE BAND INSTEAD WAS TRIED AND IS WRONG - recorded so it is not retried. Dropping the
    # row's `bound * 1.3` allowance to `bound` made Inashiro WORSE (109 -> 158 ft, houses past 150 px
    # 4 -> 8) and Mizuguchi too (65 -> 93). A front row that cannot follow the field outline does not
    # move inward; it loses its seats to the cloud, which sits further from the tracks still. The
    # row's reach past the band was never the defect - its blindness to the tracks was.
    #
    # THE FIRST `_FIELD_RING_FLOOR` SEATS ARE EXEMPT, because the ring comes first and it is a GATE
    # check where frontage is a form rule with none. Capping every seat took cohort seeds 22 and 47
    # from passing to `field_ringed` 3-of-5 and 4-of-5. This is the same concern the rank cap's floor
    # of 6 answers from its own side; both are needed, because that floor bounds the COUNT while this
    # exemption is about WHICH seats may fill it.
    _row_seats = 0
    for standoff in (46.0, 56.0, 66.0, 78.0, 92.0, 110.0, 130.0, 150.0):
        if placed >= front_cap:
            break
        for fx, fy in front_row(plan, min(plan.spec.households, 12), standoff=standoff):
            if placed >= front_cap:
                break
            if (_row_seats < _FIELD_RING_FLOOR or _lane_dist(s, fx, fy) <= _FRONT_ROW_LANE_CAP) and math.hypot(fx - seat["cx"], fy - seat["cy"]) <= bound * 1.3 and s.try_place(fx, fy, "plain"):
                placed += 1
                _row_seats += 1
    # ...then rows FLANKING the lanes, before any shape fill. A lane exists to be fronted, and a
    # cluster seeded only by its shape leaves them running across empty middle: the review of the
    # first draft measured a median house-to-lane distance of 94 ft against Ikegami's 55, with one
    # lane dead-ending in open ground and no house at its end. Offering the placer seats at exactly
    # the corridor's edge is what puts the doors on the street.
    #
    # THIS PASS IS WHAT BUILDS THE BACK RANK (2026-08-17, and the history is worth two sentences
    # because a comment here was briefly WRONG about it). For part of one day `front_row` sampled by
    # density with no cap and seated every household by itself, this pass placed nothing, and a
    # comment was written saying so - "now a fallback". Three settlement-reviews then showed what
    # that actually meant: the cluster had become a single rank along the paddy, Mizuguchi at aspect
    # 7.24 with no house standing behind any other. The cap above is the fix, and it makes THIS pass
    # load-bearing again: the households past one rank's worth are seated here, behind the front row.
    # Measured on Mizuguchi after the cap, distance from each house to the field outline falls in
    # four bands - 18/41/58/58, then 96/101/116/128, then 193/193/216, then 297 ft - and everything
    # past 150 ft (the front row's furthest standoff) came from this loop.
    #
    # WHAT THE CAP COSTS, recorded rather than left implied: fronting loosens. Mizuguchi's median
    # house-to-lane went back to ~98 ft from the ribbon's 77, with 4 of 12 within 60 ft rather than
    # 10. The ribbon's tighter fronting was an artifact of the defect, not a baseline worth keeping -
    # but ~98 is the figure an early review criticized against Ikegami's 55, and this loop is where
    # a future tightening belongs, since it is the pass now doing the seating.
    for lx, ly in lane_frontage(s, seat):
        if placed >= plan.spec.households:
            break
        if in_band((lx, ly)) and s.try_place(lx, ly, "plain"):
            placed += 1
    _cloud_placed = 0
    for attempt in range(4):
        if placed >= plan.spec.households:
            break
        # each round widens the band a little (and reaches a little further back from the field)
        wlat, wdep = lat * (1.0 + 0.22 * attempt), dep * (1.0 + 0.16 * attempt)
        want = plan.spec.households * 6 + 30
        for lx, ly in s.cluster_seeds(plan.cluster_shape, 0.0, 0.0, wlat, wdep, want, rng, record=False):
            if placed >= plan.spec.households:
                break
            # THE CLOUD LEANS TOWARD THE FIELD. `cluster_seeds` returns a shape symmetric about the
            # band's middle, which spreads a hamlet's houses as far behind the settlement as in front
            # of it - and the ground in FRONT is the ground that matters: `field_ringed` wants five
            # farmhouses within 165 px of the outline, and on a map whose near margin is largely crop
            # and ditch corridor only four of them land there. Compressing the away-from-field
            # coordinate pulls the whole cloud a quarter closer without changing its shape or count,
            # which is also how a farming hamlet really sits - the houses crowd the fields they work
            # and thin out behind.
            ly = -wdep + (ly + wdep) * 0.75
            if s.try_place(seat["cx"] + ax * lx + ox * ly, seat["cy"] + ay * lx + oy * ly, "plain"):
                placed += 1
                _cloud_placed += 1
    # THE SHAPE IS RECORDED ONLY IF THE CLOUD ACTUALLY SHAPED THE CLUSTER (2026-08-17).
    # `cluster_seeds` used to stamp `meta.cluster_shape` on its first attempt, BEFORE it knew how
    # many seats it would win - which was harmless while the cloud either ran for the whole hamlet
    # or not at all. The front-row cap changed that: the rows now seat one rank and the cloud seats
    # the SURPLUS, so on Sawada and Inashiro a knob describing a minority of the houses started
    # being stamped for the first time. It is not idle bookkeeping - `check_village/driver.py`'s
    # `TWIN_AXES` reads "the declared knob if present, else the cluster-bbox aspect", so Sawada
    # began reporting its shape as "round" to the twin detector while drawing a 3.48:1 band.
    #
    # A DECLARATION MUST DESCRIBE THE DRAWING. The cloud shaped the cluster only if it seated most
    # of it; below that the frontage rows did, and the rolled shape went unhonored exactly as it
    # does when the cloud never runs at all. `meta.cluster_seeding` still records which happened, so
    # nothing goes silent - that is the invariant `settlement_records_cluster_seeding` holds.
    # THE SHAPE IS ALWAYS HONORED NOW, so it is always declared (2026-08-19). This used to stamp the
    # knob only when the CLOUD seated most of the cluster, on the correct principle that a
    # declaration must describe the drawing - but the census behind `CLUSTER_BAND_ASPECT` showed the
    # cloud never runs at all, so the guard meant the knob was declared on no map and honored on no
    # map. It binds at the cluster BAND now (`seat_cluster`), which is what the front rows are seated
    # along, so every map both honors and declares it and `TWIN_AXES` reads a shape the sheet
    # actually has.
    # ...BUT ONLY IF THE SHEET ACTUALLY HAS THAT SHAPE. Measured, and this is the third thing the
    # shape work turned up: on a 20-household hamlet the LANE SKELETON seats most of the cluster
    # through `lane_frontage`, and a T spreads houses two ways whatever the band and the row do -
    # Kashikawa declares `elongated` and draws 1.0:1. The band and row bindings are real (Inashiro
    # 3.3:1 crescent, Mizuguchi 1.7:1 round, Sawada 1.1:1 round) but they do not outrank the
    # skeleton, so a blanket declaration would put a shape on the manifest that `TWIN_AXES` reads
    # and the sheet does not have - the same "declaration must describe the drawing" failure the
    # old cloud-only guard was written for, in a worse form because it would look honored.
    #
    # So the DRAWN aspect decides. Where the shape bound, it is declared; where the skeleton
    # overrode it, `cluster_shape_unhonored` records the roll that did not take, because a knob
    # that silently fails to bind is what this whole defect was. `cluster_shape_matches_the_drawing`
    # gates it.
    _cxs = [h["x"] for h in s.M.get("houses", [])] or [0.0]
    _cys = [h["y"] for h in s.M.get("houses", [])] or [0.0]
    _cw, _ch = max(_cxs) - min(_cxs), max(_cys) - min(_cys)
    _drawn = max(_cw, _ch) / max(1.0, min(_cw, _ch))
    _lo, _hi = CLUSTER_DRAWN_ASPECT.get(plan.cluster_shape or "crescent", (1.9, 4.2))
    if _lo <= _drawn <= _hi:
        s.M["meta"]["cluster_shape"] = plan.cluster_shape
    else:
        s.M["meta"]["cluster_shape_unhonored"] = plan.cluster_shape
    s.M["meta"]["cluster_aspect_drawn"] = round(_drawn, 2)
    # THE ROLLED SHAPE MUST LEAVE A TRACE EVEN WHEN THE CLOUD NEVER RUNS (known-open ledger
    # 2026-08-16, Kashikawa: the front rows + lane frontage seated all 20 households, the
    # cluster-seeds cloud never ran, and the rolled cluster_shape knob went unhonored with no
    # trace on the manifest - a knob that can silently not-record is the "check that never runs"
    # shape). Record the seeding mode always: "cloud" when cluster_seeds ran (it records
    # meta.cluster_shape itself), "frontage" when the rows/frontage passes seated every house and
    # the rolled shape went unhonored. `settlement_records_cluster_seeding` holds the invariant.
    # ...and this stays a SEPARATE record, keyed on what actually seated the houses rather than on
    # whether the shape got stamped. It used to be derived from the presence of `cluster_shape`,
    # which stopped meaning anything the moment the shape was always declared.
    s.M["meta"]["cluster_seeding"] = "cloud" if _cloud_placed * 2 >= max(1, plan.spec.households) else "frontage"
    plan.placed = s.farmsteads()
    # ...and NOW the lanes can be told what they actually serve. They were laid first because a lane
    # is a no-build corridor the homesteads front, so at lay time nothing knew where the houses would
    # land, and an arm that met neither crop nor water ran the whole cluster band into open ground.
    # Trimming only ever shortens, so it cannot invalidate a seat already taken. See
    # `Settlement.trim_lane_stubs` for the measurement that prompted it.
    s.trim_lane_stubs()


# ---- STAGE 6: what stands among the houses ------------------------------------------------------


def stage_appurtenances(s: Settlement, plan: SitePlan) -> None:
    """Communal wells and shared draft byres, dropped into the courtyards the homesteads left.

    AFTER the houses (they slot into the gaps the final layout produced, which is a thing only the
    finished layout knows) and BEFORE the grove (whose canopy then skips them). Both are sized off
    the houses that actually landed, not off the declared household count: a byre is roughly one per
    four or five households, and the wells cover the cluster's real extent."""
    houses = s.M.get("houses", [])
    if not houses:  # pragma: no cover - a hamlet with no houses fails the gate long before here
        return
    place_wells(s, plan, houses)
    s.draft_byres(fraction=0.22, gap=60)


def well_target(households: int) -> int:
    """How many communal draw-wells a hamlet of this size keeps.

    `wells_sized_to_population` wants 2-20 households per well at hamlet scale (the setting's
    deliberate prosperity liberty runs generous wells), so the band for 12 households is 1 to 6.
    One per ~6 households sits mid-band and matches what the authored hamlets draw - a couple of
    shared wells among the courtyards, not one per farm and not one for the whole place."""
    return max(1, min(6, round(households / 6.0)))


def place_wells(s: Settlement, plan: SitePlan, houses: Sequence[Mapping[str, Any]]) -> int:
    """Seat the communal wells INSIDE the house cloud, not on a box around it.

    The engine's `place_wells` sweeps a grid over a bbox, which is right for a town's street blocks
    and wrong for a loose farm cluster: the bbox corners are open ground, so a well lands past the
    outermost homestead and, being a hard crop feature with a 16 px extent, drags the map's frame
    out after it and leaves a band of empty scrub on that side
    (`crop_not_held_open_by_one_feature`). Insetting the bbox was tried first and is not the fix -
    it starves an elongated cluster of wells entirely, because the inset box no longer holds a grid
    cell (`settlement_has_wells`, seed 3).

    So the seats are derived from the HOUSES: a candidate must have several homesteads around it and
    none too far, which is what "among the dwellings" means, and the innermost candidates are tried
    first. `well_at` gives the engine's own verdict on each - it refuses a seat on a lane, a crop, a
    footprint or too near another well - so nothing here restates a placement rule."""
    xs = [h["x"] for h in houses]
    ys = [h["y"] for h in houses]
    ccx, ccy = sum(xs) / len(xs), sum(ys) / len(ys)
    want = well_target(plan.spec.households)
    placed: list[Pt] = []
    # A WELLHEAD MAY NOT STAND IN THE SHELTER BELT (settlement-review, Inashiro 2026-08-18). The
    # belt is drawn later, but `village_grove` SKIPS any clump whose canopy would reach a wellhead
    # (`wells_clear_of_trees` - a well lost under the grove reads wrong), so a well seated inside
    # the belt's footprint silently deletes the clumps around it. Measured on Inashiro after the
    # tie-break change moved a well to (1098,1387), inside the belt's own footprint: the 40 ft band
    # at y1360-1400 went from 8 clumps to 1, and the belt acquired its first zero-canopy latitude in
    # a 930 ft run - a hole straight through the WINDWARD side, which is the entire point of a
    # windbreak. Nothing caught it: the belt's continuity is not gated, and the well checks are all
    # about the well.
    #
    # The belt is DERIVED from the houses, which already stand, so the prospective footprint can be
    # asked for now - the same expression `stage_woodland` will call, so the two cannot disagree.
    # This is a PREFERENCE and not a veto, per this function's standing rule that a settlement with
    # a badly-placed well beats one with no well: it sorts belt seats last, so one is taken only
    # when nothing outside the belt serves at all. It also happens to push wells toward the
    # dooryards, which is where the idiom 井戸端会議 puts them.
    from .hinterland import belt_polygon  # local: hinterland is a later stage, module-level would invert the pipeline's reading order

    _belt = belt_polygon(s, plan)

    def _in_belt(c: tuple[float, float, float]) -> int:
        return 1 if _belt and point_in_poly(c[1], c[2], _belt) else 0

    # THE MINIMAX SERVES THE HOUSES THAT NEED A WELL (known-open ledger 2026-08-16): the
    # worst-served objective used to count every house, including those
    # `settlement_dwellings_watered` already treats as watered by a nearby stream / channel /
    # pond (Kashikawa's SW pocket, 77-182 ft from the stream head - the GM-settled "no redundant
    # well beside a living stream" case), so the objective and the check read two definitions of
    # "needs a well". `surface_water_dist` is the check's own predicate; a house within its
    # reach of surface water drops out of the objective and out of the rescue pass below. If
    # EVERY house is surface-watered the objective falls back to all of them - wells are still
    # dug (well_target), they just stop chasing houses the water already serves.
    _sw_reach = 760.0 / max(plan.ftpx, 0.01)
    needy = [h for h in houses if surface_water_dist(s.M, h["x"], h["y"]) > _sw_reach] or list(houses)
    # A RELAXATION LADDER, not a single rule. The tight neighborhood test is right for a compact
    # cluster and impossible for a stretched one: an `elongated` cluster strung along a margin has
    # no point with three homesteads inside 190 px, so the strict pass found nothing at all and the
    # map shipped with no well (seeds 3 and 12). A settlement WITHOUT a well is a much worse map
    # than one whose well sits a little wide, so the test loosens until it finds seats. It never
    # loosens into "anywhere": every seat still has to be nearer a house than the crop.
    # Only the THIRD-nearest distance relaxes - the "is this in a neighborhood" test. The distance to
    # the NEAREST house stays tight, because `wells_among_dwellings` is a 95 px gap verdict against
    # the served building's edge: a well 220 px from its closest farmhouse is standing in the fields
    # by any measure, and relaxing that rung traded one failure for another.
    # The last rung also serves a PAIR. Every rung above asks for three homesteads around a seat,
    # which is the right shape for a nucleus and leaves a two-farm satellite with no well of its own
    # - and then the coverage pass cannot rescue it either, because the ground among two farms is
    # their own courtyards. Seed 18 stranded exactly that: a pair 500 px off the cluster, 760 and
    # 777 px from the nearest well, with all 118 legal-neighborhood probes around them refused.
    # Two households sharing a draw-well is an ordinary thing; three is not a threshold nature knows.
    for third, nearest, want_near in ((190.0, 105.0, 3), (300.0, 110.0, 3), (520.0, 112.0, 3), (520.0, 112.0, 2)):
        if len(placed) >= want:
            break
        seats: list[tuple[float, float, float]] = []
        step = 22.0
        # THE SWEEP BOX IS THE HOMESTEADS', NOT THE HOUSE CENTERS' (2026-08-15, cohort seed 44).
        # A bundle's courtyard ground extends ~a house-length past its house CENTER, so a cluster
        # strung along its field margin can keep every legal well pocket just OUTSIDE the centers'
        # bbox - seed 44 had 84 legal seats, nearly all north-west of min(xs)/min(ys), and the
        # unpadded grid visited none of them (0 of 1440 probes passed; the map shipped well-less).
        # The pad only restores ground the bundles themselves cover: every rung still demands
        # near[0] <= ~105 px, so an open-field corner of the padded box is rejected exactly as the
        # docstring above promises.
        pad = 120.0
        y = min(ys) - pad
        while y <= max(ys) + pad:
            x = min(xs) - pad
            while x <= max(xs) + pad:
                near = sorted(math.hypot(x - h["x"], y - h["y"]) for h in houses)
                if len(near) >= want_near and near[want_near - 1] <= third and near[0] <= nearest:
                    seats.append((math.hypot(x - ccx, y - ccy), x, y))
                x += step
            y += step
        # GREEDY COVERAGE, not central-first throughout (settlement-review, Mizuguchi/Sawada
        # 2026-08-15): sorting every well toward the centroid put both of Mizuguchi's wells in one
        # lobe of a two-lobed cluster - the six eastern households walked 248-424 ft while the west
        # had a well within 63. The FIRST well is central (innermost legal seat, as before); every
        # LATER well takes the legal seat FARTHEST from the wells already standing, ties toward the
        # center - i.e. it serves the households the placed wells do not, which is why a real hamlet
        # digs a second well at all.
        pool = sorted(seats, key=lambda c: (_in_belt(c), c[0]))  # the FIRST well is central too, but never in the belt if anywhere else will do
        while pool and len(placed) < want:
            if placed:
                # ...by MINIMAX NEED, in ~3-grid-step buckets, centrality breaking ties inside a
                # bucket. Two failed rankings led here, and both are worth remembering. Strict
                # farthest-first (the 2026-08-15 greedy-coverage fix) let a seat 91 px OUTSIDE the
                # cluster beat an interior seat covering the same households - the exterior well
                # held Sawada's whole frame open (crop_not_held_open_by_one_feature). Bucketing
                # that same farthest-first score fixed the frame and re-broke coverage the other
                # way: on Mizuguchi the spread rung walked EAST past the last house into scrub
                # while the one under-served household stood at the WEST end (settlement-review
                # 2026-08-16). Both fail because "far from the standing wells" is a proxy for the
                # real quantity, which is the walk of the household WORST served after the well is
                # dug - so score that directly: pick the seat minimizing the farthest any house
                # would remain from its nearest well. A seat past the row's end cannot beat an
                # in-row seat (it serves nobody the row seat does not), and a seat in an unserved
                # lobe wins outright, which is what the greedy fix was for in the first place.
                def _worst_after(c: tuple[float, float, float]) -> float:
                    return max(
                        min(
                            min(math.hypot(h["x"] - wx, h["y"] - wy) for wx, wy in placed),
                            math.hypot(h["x"] - c[1], h["y"] - c[2]),
                        )
                        for h in needy
                    )

                # AND AN INTERIOR SEAT BEATS A PADDED ONE THAT SERVES THE SAME HOUSEHOLDS. The sweep
                # box above is padded 120 px past the house CENTERS because a bundle's courtyard
                # really does reach that far, and without the pad seed 44 shipped well-less. But the
                # pad is symmetric, so it equally offers seats BEYOND the outermost homestead on
                # every side - and a wellhead is a hard crop feature with a 16 px extent, so one
                # seated out there drags the map's frame after it and leaves a band of empty scrub
                # (`crop_not_held_open_by_one_feature`). The RESCUE pass below already refuses
                # exactly that, with its `min(xs) <= x <= max(xs)` test and a comment giving this
                # very reason; the greedy pass did not - two passes carrying two definitions of
                # "inside the house cloud", with the looser one running first.
                #
                # MEASURED on cohort seed 41: the second well won its minimax bucket on the strength
                # of one north-east household, then seated 76 px NORTH of that household and 66 px
                # past every other feature on the map. The minimax objective is right and is not
                # what moved here - the tie-break was, because distance-to-centroid cannot express
                # "this seat is outside the settlement".
                #
                # SO IT IS A TIE-BREAK AHEAD OF CENTRALITY, NOT A FILTER. The padded ground stays in
                # the pool and still wins when nothing inside the cloud serves the same households,
                # which is what the pad was added for; it simply can no longer outrank an interior
                # seat that does. Same shape as every other rule in this function: relax rather than
                # forbid, because a settlement with a badly-placed well beats one with no well.
                # OUTSIDE WHAT, EXACTLY - the CROP's own box, not a box round the house CENTERS. The
                # first version of this tie-break tested `min(xs)..max(xs)`, an AABB of house centers,
                # and settlement-review (Inashiro 2026-08-17) named the flaw before it bit: an AABB
                # cannot tell "in the settlement" from "in the box", so on a two-lobed cluster the
                # ~345 px of grove and scrub BETWEEN the lobes scores as interior, exactly like a
                # courtyard. Cohort seed 29 then did bite - a well 64 px north of every other feature,
                # inside the centers' box and holding the whole frame open.
                #
                # `_crop_boxes` is what `crop_to_content` itself reads, so asking it is asking the
                # question the check will ask: a seat inside the box the crop will set cannot hold the
                # frame open, whatever its relation to the house centers. Same-source doctrine, and it
                # picks up the houses' DRAWN extents plus their yards, gardens, sheds and byres rather
                # than a point per house. (The box can only GROW later - the woodland and the pond are
                # placed after - so this is conservative in the safe direction.)
                _cb = s._crop_boxes(city=False)
                _bx0 = min((b[0] for b in _cb), default=min(xs))
                _bx1 = max((b[1] for b in _cb), default=max(xs))
                _by0 = min((b[2] for b in _cb), default=min(ys))
                _by1 = max((b[3] for b in _cb), default=max(ys))

                # A TIE-BREAK CANNOT REACH A SEAT WITH NO RIVAL IN ITS BUCKET, so the FRAME goes into
                # the score itself. Ranking outside-ness ahead of centrality fixed cohort seed 29 and
                # left seed 7 failing for the reason a tie-break always leaves one: its pad seat was
                # alone in its minimax bucket, so there was nothing to break the tie against. Seed 7's
                # well sits 25 px past the northernmost byre and holds the whole frame open
                # (`crop_not_held_open_by_one_feature`), because a wellhead is a hard crop feature with
                # a 16 px extent and the crop follows it out.
                #
                # THE EXCHANGE RATE IS 1:1 IN PIXELS, which is what makes this a rule rather than a
                # knob: a seat that drags the frame out by N px must save at least N px of the
                # worst-served household's walk to be worth it. Both quantities are distances in the
                # same units, so no weighting has to be invented - and the well that genuinely serves
                # an outlying lobe still wins, because the coverage it buys is real.
                def _extent_added(c: tuple[float, float, float], bx0: float = _bx0, bx1: float = _bx1, by0: float = _by0, by1: float = _by1) -> float:
                    """How far past the crop's predicted box this seat (drawn radius included) reaches."""
                    return max(0.0, bx0 - (c[1] - _WELL_DRAWN_R), (c[1] + _WELL_DRAWN_R) - bx1, by0 - (c[2] - _WELL_DRAWN_R), (c[2] + _WELL_DRAWN_R) - by1)

                # ...AND THE LAST TIE-BREAK IS THE NEIGHBORHOOD, NOT THE CENTROID (settlement-review,
                # Sawada 2026-08-18). Once the minimax bucket and the frame term are equal, the
                # remaining sort was `c[0]` - the seat's distance to the cluster CENTROID, computed
                # when the pool was built. On a ONE-lobed cluster that reads as "the most central
                # seat wins" and is fine. On a TWO-lobed one the centroid is the empty ground
                # BETWEEN the lobes, so the tie-break actively prefers the gap: Sawada's second well
                # moved off a seat serving 11 households within 300 ft onto one serving 5, and the
                # worst walk went 364 -> 493 ft. Same family as the `_extent_added` fix above and as
                # the standing rule against letting an aggregate stand in for the distributed thing
                # a verdict is about - a centroid is not a place anybody lives.
                #
                # The measure that IS the question: how tightly is this seat surrounded by
                # homesteads - the distance to the `want_near`-th nearest house, which is exactly
                # the rung's own "is this in a neighborhood" test, reused rather than restated.
                # Distance to the SINGLE nearest house was the ledger's sketch and is rejected: it
                # is minimized by hugging one outlying farmhouse, which is the same mistake in the
                # other direction. Every seat in the pool already passed the rung, so this only
                # orders seats that are all legally "among the dwellings".
                def _neighborhood(c: tuple[float, float, float], wn: int = want_near) -> float:
                    return sorted(math.hypot(c[1] - h["x"], c[2] - h["y"]) for h in houses)[wn - 1]

                # THE BELT TERM SITS BEHIND COVERAGE, not in front of it. Ranked first it is a
                # filter, and it behaved like every other filter this function has tried: Mizuguchi's
                # second well moved off a seat inside the belt and its worst walk went 203 -> 264 ft,
                # on a map whose belt hole turned out not to be well-caused at all, so the trade
                # bought nothing. Behind the minimax bucket it can only decide between seats that
                # serve the households equally well - which is all "do not stand in the windbreak"
                # was ever entitled to decide.
                pool.sort(key=lambda c: ((_worst_after(c) + _extent_added(c)) // 66.0, _in_belt(c), _extent_added(c), _worst_after(c), _neighborhood(c)))
            _, x, y = pool.pop(0)
            if any(math.hypot(x - px, y - py) < 170.0 for px, py in placed):
                continue  # `wells_not_clustered`: shared wells serve separate courtyards
            if s.well_at(x, y):
                placed.append((x, y))
    # ...then a COVERAGE pass. `settlement_dwellings_watered` gives every dwelling ~760 real feet to
    # the nearest well, channel, pond or stream - generous, and still not automatic once a cluster is
    # sized from the real bundle pitch and runs 700+ px along its margin: a single well at one end
    # leaves the far end dry. So any house still out of reach gets a well sought beside it.
    reach = 760.0 / max(plan.ftpx, 0.01)
    for h in houses:
        if any(math.hypot(h["x"] - px, h["y"] - py) <= reach for px, py in placed):
            continue
        if surface_water_dist(s.M, h["x"], h["y"]) <= reach:
            continue  # watered by a stream/channel/pond - the check's own verdict; no rescue well
        # A RING PROBE, spiraling out from the house, asking `well_at` directly.
        #
        # AND EVERY CANDIDATE MUST STILL STAND AMONG THE DWELLINGS - near SOME house, not necessarily
        # the one being rescued. `wells_among_dwellings` is a 95 px edge-gap verdict against the
        # served building, and this probe used to take the first seat `well_at` allowed at any radius
        # out to 340. That was harmless while nothing reached this branch, and stopped being harmless
        # the moment the sun corridor (2026-08-13) spread a cluster enough to strand a household:
        # seed 18 seated a well 161 px from its nearest dwelling. Capping the RADIUS was the obvious
        # fix and the wrong one - it just traded the failure for `settlement_dwellings_watered`,
        # leaving the household dry. The honest constraint is the one the check states: a well may
        # be dug well away from the farm it rescues, as long as it is in somebody's courtyard.
        #
        # `open_seat` was tried here first and is the wrong tool: it optimizes a seat over a
        # RECTANGLE - furthest from what it is told to clear, ties toward the center - and it
        # returned None at every radius from 60 to 430 px around a stranded farmstead that had a
        # perfectly legal spot 40 px to its east. What this needs is not the best seat in a region
        # but ANY seat near THIS house, so it asks the question that way round, and it asks it of
        # `well_at`, which is the call that actually places a well.
        spot = None  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
        for radius in range(40, 340, 20):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
            for bearing in range(0, 360, 20):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                cand = (
                    h["x"] + math.cos(math.radians(bearing)) * radius,
                    h["y"] + math.sin(math.radians(bearing)) * radius,
                )  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                if not (
                    min(xs) <= cand[0] <= max(xs) and min(ys) <= cand[1] <= max(ys)
                ):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    # a rescue well still sits INSIDE the house cloud. A wellhead is a hard crop  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    # feature with a 16 px extent, so one seated past the outermost homestead drags  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    # the frame out after it (`crop_not_held_open_by_one_feature`) - the same reason  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    # the grid above is laid over the cloud rather than a box grown around it.  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    continue  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                if not any(math.hypot(cand[0] - hh2["x"], cand[1] - hh2["y"]) <= 95.0 for hh2 in houses):  # pragma: no cover - the rescue's among-the-dwellings floor
                    continue  # pragma: no cover - center distance <= 95 is strictly inside the check's 95 px EDGE gap
                if any(
                    math.hypot(cand[0] - px, cand[1] - py) < 110.0 for px, py in placed
                ):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    continue  # `wells_not_clustered`: shared wells serve separate courtyards  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                if s.well_at(cand[0], cand[1]):  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    spot = cand  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                    break  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
            if spot is not None:  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                placed.append(spot)  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
                break  # pragma: no cover - the well ring-probe rescue; the bundle-pitch fix left the courtyards open enough that no cohort map strands a household
    if not placed:
        # LAST RESORT: ask the engine. A settlement with NO well fails the gate outright, and by
        # this point the lattice has been refused everywhere - which means the courtyards are full,
        # not that there is no room. `open_seat` runs the engine's own `_fits` over the ground and
        # returns the best clear spot or None, which is the documented answer to "this pocket needs
        # one more X" and finds seats a hand-rolled scan misses (the skill's dev notes: a manifest
        # scan cannot predict `_fits`).
        spot = s.open_seat(
            (min(xs), min(ys), max(xs), max(ys)), 16.0, 16.0, well=True
        )  # pragma: no cover - reached only when the lattice above found NOTHING, which the bundle-pitch fix made rare; a settlement with no well fails the gate outright, so the branch stays
        if spot is not None and s.well_at(spot[0], spot[1]):  # pragma: no cover - the last-resort seat; unreached since the bundle-pitch fix left the courtyards open
            placed.append(spot)
    return len(placed)
