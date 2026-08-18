"""Layer-1 bank clearance: how plots hem to supply canals and delivery ditches (clearance, toe, overhang), plus channel-joint rounding."""

import math
from typing import Any

from .frame import BANK_MARGIN, Poly, Pt, _f_at_u, _Frame, _pip, _seg_x, taper_w

_PAST_EPS = 0.25  # arc slack at a supply stroke's ends: covers the 0.1-px manifest rounding of vertex + stroke point together (see supply_bank_clearance)


def polyline_cum(pts: Poly) -> list[float]:
    """Cumulative arc length at each vertex - hoisted so a caller testing many points against one
    collector pays for it once."""
    cum = [0.0]
    for i in range(len(pts) - 1):
        cum.append(cum[-1] + math.dist(pts[i], pts[i + 1]))
    return cum


def taper_pieces(pts: Poly, w0: float, w1: float) -> list[tuple[Poly, float]]:
    """A tapering stroke split into drawable pieces, each carrying its ARC-CORRECT local width.

    PARAMETERIZED BY ARC LENGTH, NEVER BY VERTEX INDEX - which is the bug this replaced
    (settlement-review 2026-08-17). `field_channel` used to cut the polyline into 7 equal slices of
    the INDEX range and give slice k the width at `(k + 0.5) / 7`, which is only the width at that
    point of the run if the vertices are evenly spaced along it. The carve's are not: measured on
    Inashiro, one delivery ditch's seven slices covered 7.0 / 9.2 / 3.2 / 4.2 / 15.9 / 27.5 / 33.0%
    of its length, so the drawn width missed the law by up to 1.94 px (24-44% of the local width),
    the last third of the ditch was drawn at a FLAT minimum - the very "reaches the minimum and just
    stops" reading the taper work set out to fix - and a 2-point stub had six empty slices and was
    drawn end to end at its TAIL width, 3.6 px where its own record declared a 7.2 px head.

    Per SEGMENT rather than in buckets, for two reasons beyond correctness: a bucket boundary is a
    visible step (1.84 px in one place on the collector), and `banks.py`, `seams.py` and `carve.py`
    already take their local width at the arc fraction - so drawing per segment makes the INK agree
    with the bank geometry the bunds are laid against and the gate re-measures, rather than merely
    coming close to it.

    ONE definition, shared by the renderer (`field_channel`) and the keep-out corridor
    (`_watercourse_segs`), which used to build this ladder separately and identically - two copies
    of one ladder is how the drawn stroke and the corridor that protects it drift apart.

    KNOWN BOUND, measured rather than assumed (settlement-review 2026-08-17). The ink is piecewise
    constant per segment, while the two bank clearances below and `close_seams`' buffer evaluate the
    CONTINUOUS law at the query point - so the drawn edge and the geometry the bunds are laid
    against differ by up to half the step between neighboring pieces. On Inashiro that is 0.11-0.14
    px on most strokes, 0.21-0.23 on the two coarse-tailed deliveries, 0.52 on the collector, and
    **1.19 px on the 2-point stub**, where one piece has to stand for a run whose law goes 7.2 ->
    3.2; the stub's nearest plot ring ends up +0.25 px clear of the drawn edge against a designed
    `BANK_MARGIN` of 0.75. Nothing crosses on any shipped map, so this is a shrunken abutment, not a
    bund in the water. IF IT IS EVER WORTH CLOSING: have `drain_bank_clearance` /
    `supply_bank_clearance` / the `half` closure in `seams.py` take `t` at the arc midpoint of the
    segment they already identify as nearest, instead of at the query point's own arc fraction -
    they each compute that segment's index and `arc` already, so it is a few lines each. It re-rolls
    every scripted map, so it wants its own pass with a `settlement-review` per map. The alternative
    fix - densifying the polylines before stroking - would also close the collector's residual 1.64
    px step notch at (1521.7, 1540.7), which the per-segment split did not remove because that
    stroke has only 10 vertices over 1240 px."""
    if len(pts) < 2:
        return []
    cum = polyline_cum(pts)
    tot = cum[-1] or 1.0
    return [([pts[i], pts[i + 1]], taper_w(w0, w1, (cum[i] + cum[i + 1]) / 2 / tot)) for i in range(len(pts) - 1)]


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
    need = taper_w(w0, w1, arc / (cum[-1] or 1.0)) / 2 + BANK_MARGIN
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
    halfw = taper_w(w0, w1, arc / (cum[-1] or 1.0)) / 2
    # `past` IS ROBUST AT THE MANIFEST ROUNDING SCALE (the seed-25 hairline, 2026-08-16): the
    # placer works in unrounded floats and exempted a carved corner projecting epsilon PAST the
    # branch tail; the manifest rounds both the corner and the stroke poly to 0.1 px, which
    # collapsed them onto the same coordinates - the gate then computed t = 1.0 exactly, `past`
    # came back False, and the check fired at gap 0 on a corner the placer had legally exempted.
    # One predicate, two verdicts, split by the round-trip. So ground within _PAST_EPS of either
    # end of the stroke's arc counts as past on BOTH sides of the rounding (same class as the
    # gate's 0.15 gap slack).
    past = past or arc <= _PAST_EPS or arc >= (cum[-1] or 1.0) - _PAST_EPS
    return off, halfw, past, foot, nrm


def floor_overhang(pts: Poly, dpts: Poly, down_deg: float) -> list[float]:
    """Per-vertex DOWN-FALL overhang past the flat-extended collector line, in px (0 = clear).

    The fan's command area ends at its collector: ground down-fall of the drain line - extended
    LEVEL beyond both drawn ends, exactly as `_fill_wedges`' `drain_f_clamped` extends it - cannot
    drain into it and is never planted, so field floor there is dead ground wearing the field's
    color (Mizuguchi's SE needle, 2026-08-16: the raw envelope closed from the collector's thin
    head across ~350 ft of bare floor to the outer thread's tail). ONE predicate, shared by
    `build_comb`'s envelope trim and by the gate (`comb_floor_ends_at_the_collector`), for the
    same reason `supply_bank_clearance` is: a trimmer and a checker that classify the same ground
    from two formulas drift into disagreeing about where the command area ends."""
    F = _Frame(down_deg)
    u0 = F.to_uf(*dpts[0])[0]
    u1 = F.to_uf(*dpts[-1])[0]
    out: list[float] = []
    for p in pts:
        u, f = F.to_uf(*p)
        fd = _f_at_u(F, dpts, u)
        if fd is None:  # off either end past the interp slack: the boundary continues LEVEL
            end = dpts[0] if abs(u - u0) <= abs(u - u1) else dpts[-1]
            fd = F.to_uf(*end)[1]
        out.append(max(0.0, f - fd))
    return out


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
# ...and a SECOND, independent way to be unbundable, because thickness alone misses it. A wedge
# that tapers to a point can carry a respectable inradius while its last yards are unworkable: at
# 7.5 deg a plot is 5 ft wide 40 ft back from its apex and 2.6 ft at 20 ft, and an aze is ~1.5 ft
# of puddled mud (AZE_FT) on EACH side, so the tip is two bunds with no floor between them. The
# thickness proxy passed those because they are LONG - 130-254 ft on Inashiro - which is how the
# fan-toe sunburst survived the toe pass (GM ruling 2026-08-17: the fan's narrowing shape is real,
# these angles are not). 25 deg is not a new number: it is `pointed_ring`'s own measured carve
# threshold (pool-wide, seam wedges run 7-23 deg and honest hem strips 45+), and the gate
# `paddy_plots_are_workable_basins` fires at 15 - placer stricter than gate, as everywhere else.
_TOE_MIN_APEX = 25.0
# THE WELD GETS ITS OWN, TIGHTER MARGIN, because refusing is not free there. The carve and `_plant`
# can refuse a needle at a generous 25 deg and lose nothing: the ground simply returns to the bare
# pocket for `close_seams` to place another way. `_absorb` is the LAST resort - refuse there and the
# scrap stays bare between two basins that each still draw their own wall, which is precisely the
# doubled bund `paddy_plot_seams_shared` exists to prevent. Measured on the 24-seed cohort: a 25 deg
# weld guard traded two needles for two doubled bunds (seeds 9 and 11) and took the cohort 22 -> 20.
# Every weld it declined in the 15-25 band would have produced a basin the gate ACCEPTS, so the
# generous margin was buying nothing and costing a real defect. This sits just above the gate's 15
# with enough room that rounding cannot slip a needle through.
_WELD_MIN_APEX = 18.0
# THE TINT DEMOTION ASKS A DIFFERENT QUESTION, so it measures a different ring - not a different
# threshold. Two settlement-reviews shaped this, and the second corrected the first.
#
# Sawada (2026-08-17) found the demotion had gone structurally DEAD: it tested apexes below 25 deg,
# the needle fix set the placer's own floor to the same 25, so after the fix no ring below 25 exists
# and the predicate could never fire - while the sharpest survivors piled up on its boundary and one
# 91 x 18 ft blue wedge missed demotion by 0.05 deg on the map briefed "no pond". The first fix was
# to raise the threshold to 40. THAT WAS WRONG, in both directions, and Inashiro's review measured
# it: raising it demoted a 35.5 x 118.3 ft strip keeping 82% workable floor (an honest basin), while
# still passing plot 456, which tapers 30.0 -> 3.4 ft over 75 ft and scores 49.6 deg only because its
# needle is TRUNCATED 8 ft short of the point. The claim that 25-40 is an empty band was also simply
# false - 15 plots sit in it on that map alone.
#
# THE REAL DISCRIMINATOR IS THE END, NOT THE CORNER. What makes a blue plot read as a pond is coming
# to a POINT; an interior angle cannot see a taper whose tip has been cut off, and a long honest
# strip can carry one sharpish corner. So the threshold goes back to 25 and the ring is DEDUPED AT AN
# END WIDTH first: an end narrower than `_TINT_END_FT` collapses to a single vertex, and the wedge
# then shows the apex it really has. That also un-deadens the predicate without a threshold race -
# it is now a different MEASUREMENT from the placer's guard rather than a number sitting next to it.
#
# 5 ft is the narrowest end that can hold water at all: two aze at AZE_FT 1.5 each is 3 ft of wall,
# leaving ~2 ft of standing water between them. Below that a basin has no end, it has a point.
_TINT_MIN_APEX = 25.0
_TINT_END_FT = 5.0
# The GATE's own line, kept here so the placer margins above are all expressed against ONE number
# rather than each carrying a copy of it. `paddy_plots_are_workable_basins` fires below this; every
# constant above it is a margin over it, and the invariant the calibration rests on is that all of
# them are strictly greater.
_GATE_MIN_APEX = 15.0
# ...and a THIRD way to be unworthy of a bund of its own, which is neither thinness nor a point:
# being TOO SMALL RELATIVE TO THE FAN IT SITS IN. GM question 2026-08-17, reading a hamlet sheet:
# "most of the rice paddy fields are rectangular, but then there are a few very small triangles ...
# should there be a minimum rice paddy size? I would expect that there would be."
#
# THERE IS NO ABSOLUTE MINIMUM, AND THAT ANSWER IS RESEARCHED RATHER THAN ASSUMED. Shiroyone
# Senmaida works 1,004 basins on about 4 ha: the average runs ~18-20 m2 and the smallest is roughly
# half a meter square - two rice stalks - with the local anecdote that a paddy once reported missing
# turned up under a straw raincoat. Our smallest scripted-hamlet basin is 240 sq ft (~22 m2), which
# is LARGER than a typical Senmaida paddy. Any floor stated in acres would therefore condemn the
# most famous paddies in Japan, so the absolute floor was priced and DECLINED (research/fields.md).
#
# WHAT IS REAL IS A RATIO, AND THE REASON IS THE AZE. On a terrace the wall a basin needs already
# exists: the riser is a structural retaining wall the slope demands whether or not anyone
# subdivides, and the water is held by a 10-15 cm lip on top of it - so the marginal cost of one
# more tiny bench is near zero and the alternative to it is bare rock. On a valley-floor cascade fan
# there is no riser. The aze IS the whole structure, built only to hold water, and it costs its own
# strip of the most valuable land on the map plus a full perimeter of azenuri re-plastering every
# spring. The alternative to a scrap here is never "no rice": it is making the basin NEXT DOOR
# bigger, which costs no new wall at all. That is this module's own research answer for an awkward
# scrap - "taken into the basin beside it rather than walled off on its own" - applied to SIZE.
#
# WHERE THE LINE SITS, BY TWO INDEPENDENT ROUTES THAT AGREE (the pattern the drain-head width note
# already uses, and the reason 0.25 is not a compromise). (1) GEOMETRY: a quarter of the design
# cell's AREA is half its linear size in both directions, so below it a parcel is not a cell that
# came out small, it is a fragment of one. (2) COST: the aze eats a share of the ground it encloses
# that climbs as the basin shrinks - at AZE_FT 1.5 with half charged to each side, a hamlet's 38.6 ft
# design cell pays 8.1%, and 19.2 ft pays 16.2%. 0.25 of the cell is exactly the square at which
# that overhead has DOUBLED off its design value. The two routes land on 0.25 together, and they
# keep landing there at other scales because the doubling point moves so slowly: at the village
# 47 ft cell (6.5% -> 13%) it is 0.256, at 38.6 ft it is 0.248.
#
# THE THICKNESS RULE ALREADY IMPLIED A FLOOR NEAR 0.16, WHICH IS WHY THE DEFECT LOOKS THE WAY IT
# DOES - worth stating, because it explains both the shape of the tail and why the gate line below
# is where it is. `_TOE_MIN_THICKNESS` demands an inradius of 0.16 * plot_across, and for a compact
# basin the inradius is half the side, so it bottoms out at (0.32 * plot_across)^2 - about 0.16 of
# the cell. Measured with the floor patched off, the smallest basin on any of the four scripted
# hamlets is 0.160 of its cell and NOTHING sits below that. So the ground this rule newly covers is
# the narrow band 0.16-0.25: real, compact, honestly-angled parcels that are simply fragments. That
# band is exactly what the GM was looking at.
#
# THE COST WAS MEASURED BEFORE THE NUMBER WAS CHOSEN, against each fan's OWN recorded cell (an
# earlier pass measured against `paddy_grain(ftpx)` and was wrong by ~1.5x, because `plot_texture`
# had already scaled the hamlets' target down to 1,488 sq ft): over the 2,829 basins of the four
# scripted hamlets, 1.63% sit under 0.25 of their cell and 0.46% under 0.20. Nothing is LOST -
# every basin under the floor is absorbed into the one it shares the most bund with, so planted
# area, the field outline and the household COUNT are all untouched.
#
# BUT THE HOMESTEAD POSITIONS ARE NOT, and that has to be said here rather than discovered later
# (settlement-review, Inashiro 2026-08-17, correcting this comment's first draft, which had copied
# the paddy-CELL note's "farmhouse rings are unchanged" - true there, false here). The cell change
# subdivided the same envelope and drew the same number of things; this rule changes the NUMBER of
# drawn plots, and the patchwork draws from the SHARED placement RNG, so every downstream placement
# re-rolls.
#
# MEASURED, and SAY WHICH METRIC - the first write-up did not, and was wrong by 2-4x because of it
# (settlement-review, Sawada). "Up to 78 px" was each new house's distance to the NEAREST OLD house,
# which quietly lets one old house partner several new ones and so always under-reports. Under a
# real one-to-one matching (the smallest possible LARGEST displacement) the same map moves a
# household 286 px. Against main's tip - houses unmoved, then min-max displacement:
#
#   Inashiro    0 of 15   564 px   gardens 18 -> 17, farm sheds 6 -> 3, view shifts
#   Kashikawa  20 of 20     0 px   byte-identical, view included
#   Mizuguchi   7 of 12   250 px   gardens 16 -> 17, farm sheds 2 -> 1
#   Sawada     11 of 19   540 px   gardens 20 -> 23, farm sheds 5 -> 6
#
# The household COUNT holds on all four (15/15, 20/20, 12/12, 19/19) and so does the acreage - it is
# the positions that rotate, by a map-specific amount, and Kashikawa proves the amount can be zero.
# Any future rule that changes a drawn COUNT carries the same ripple; MEASURE it rather than reason
# about it, because the reasoning that feels safest ("the field outline is the same, so the rings
# that key off it are the same") is exactly the one that fails. It is also how the cohort seed-41
# well regression happened: a well moved, not a paddy.
#
# DELIBERATELY COMB-ONLY. `build_terraces` and `build_ribbon` are the hill-rice engines, and hill
# rice is exactly where the Senmaida micro-basins above are real; `build_polder`'s parcels are
# grounded true-scale on Buck's ~1 mu figure and are not cascade basins at all. Only the valley-floor
# fan carries this floor, because only there is the aze a pure, unshared cost.
_TOE_MIN_AREA = 0.25
# THE GATE'S OWN LINE, and it is NOT 0.6 of the placer's the way the apex pair is 15 of 25. It
# cannot be: the thickness rule's implicit floor sits at ~0.16, so a gate at 0.15 would be a check
# that can never fire - the failure mode this package's own doctrine names first ("a check that
# never RUNS looks exactly like a check that passes"), and it was measured, not guessed, when 0.15
# passed on a manifest generated with the floor switched off. The band the placer newly refuses is
# [0.16, 0.25), so the gate takes the MIDDLE of that band: clear of the placer by 25% so no rounding
# can make the two disagree, clear of the implicit floor by the same, and firing at once on any
# regression that reopens the band. On the pre-floor manifests it flags 2 basins on Inashiro, 1 on
# Kashikawa, 4 on Mizuguchi and 6 on Sawada; two of those are frozen in pool/regressions/.
_GATE_MIN_AREA = 0.20
# A WELD MUST NOT MAKE A LUMP OUT OF THE BASIN THAT TAKES THE SCRAP, which is the size rule's own
# second-order defect and was found by settlement-review on the first pass (Sawada and Mizuguchi,
# 2026-08-17). `_absorb` ranks candidate hosts by SHARED BUND LENGTH, which is the right first
# preference and is blind to the shape it produces: on Mizuguchi it handed a 306 sq ft fragment to
# the single lumpiest basin on the sheet and made it worse - 26 vertices, eight reflex corners, and
# four out-and-back prongs whose tips are 5-11 ft wide, each of which draws as a bund with a FREE
# END sticking into the paddy. That is the GM's "rendering artifact" complaint transplanted from
# area to outline, and it is a real construction error either way: a wall that goes out eleven feet
# and comes straight back retains water on neither side and costs a full share of azenuri.
#
# SOLIDITY (area / convex-hull area) is the measure, because the defect is CONCAVITY and the two
# guards already in the ladder both measure an APEX - `pointed_ring` cannot see a lobe whose every
# corner is blunt. Measured over the 20 absorbed basins of the first Sawada pass: eighteen scored
# >= 0.90 and the two the reviewer picked out by eye scored 0.731 and 0.78. 0.85 is the gap between
# those populations, and it is wide - nothing sits between 0.78 and 0.90.
#
# IT IS A PREFERENCE, NOT A VETO, for the reason the apex guard learned the hard way: refusing
# outright trades a lump for a doubled bund, which is worse. A lumpy weld is remembered and the
# next-best host tried; the best of the lumpy candidates is taken only if no host is clean.
_WELD_MIN_SOLIDITY = 0.85
# ...and the same measure guards the TINT, for a defect the apex guards likewise could not see
# (settlement-review, Sawada 2026-08-17). Absorbing a fragment into the fan's ONE flooded plot grew
# it a lobe: 94 x 24 ft became 94 x 38 ft at solidity 0.731, and at fit zoom it reads as an
# arrowhead POND - on the map whose brief is explicitly "no pond". `_TINT_MIN_APEX` scored it 41.8
# deg and `_TINT_END_FT` found both ends far wider than 5 ft, so both passed a plot that fails the
# thing the tint rule is actually for. Blue means "the closing rank pooling before the outfall", so
# a blue plot has to READ as a leveled basin; the same 0.85 demotes it to rice green, and the check
# runs after the absorb pass because that is what reshaped it.
_TINT_MIN_SOLIDITY = 0.85


def cell_area(plot_across: float, row_step: tuple[float, float]) -> float:
    """The fan's DESIGN cell in px^2 - the area one carved paddy was aimed at.

    ONE expression, so the placer's floor and the gate's read the same reference (the same-source
    doctrine). `row_step` is a (min, max) band, so the cell takes its midpoint."""
    return plot_across * (row_step[0] + row_step[1]) / 2.0


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


def tapers_to_a_point(poly: Poly, end: float, min_deg: float, arm: float) -> bool:
    """Does this ring run out to a TRUNCATED point - a short end edge capping two converging sides?

    The honest form of the question `dedup_ring(r, end)` was standing in for (settlement-review,
    Inashiro 2026-08-17). Deduping at an end width does collapse a truncation, but it is a GLOBAL
    operation: it merges short edges anywhere on the ring, so a staircase of chamfers in the middle
    of a perfectly good basin fuses into a spike that was never there. Four measured fabrications on
    one roll - ring #550 whose SHARPEST real corner is 86.7 deg reported 2.3 after collapsing 4.0 /
    2.4 / 4.2 ft edges, and ring #622 (83.7 -> 20.1) sat at the east toe inside the flooded candidate
    zone, one roll away from demoting an honest basin.

    So the test is per-EDGE and local. A short edge is an END only if the sides it caps are real
    basin walls: both neighbours at least `arm` long. Collapse that one edge (never a chain) and the
    angle between the two arms is the apex the wedge would have had if the toe had not cut it off -
    which is what "reads as a point" means, and is invariant to how deep the truncation went.

    `arm` is 4x the end width: a staircase's neighbours are themselves short, so requiring the arms
    to be several times the end separates a capped taper from a chamfered corner without tuning."""
    n = len(poly)
    if n < 4:
        return False
    for i in range(n):
        b, c = poly[i], poly[(i + 1) % n]
        if math.dist(b, c) >= end:
            continue
        a, d = poly[i - 1], poly[(i + 2) % n]
        if math.dist(a, b) < arm or math.dist(c, d) < arm:
            continue  # a chamfer between two short steps, not the end of a taper
        # AND THE RING MUST ACTUALLY BE WIDER BACK THERE. The angle between the two backward arms is
        # the apex angle only when they DIVERGE; for parallel sides it is 0, which reads as
        # "maximally pointed" while describing a strip of constant width. Measured on Inashiro, that
        # is not hypothetical - ring #633 is a parallel-sided strip with a 2.3 ft chamfer and scored
        # converge = 0.0 exactly. A taper is narrow HERE and wide THERE, so require the far ends of
        # the two arms to stand at least 3x the end edge apart before the angle means anything.
        if math.dist(a, d) < 3.0 * math.dist(b, c):
            continue
        v1 = (a[0] - b[0], a[1] - b[1])
        v2 = (d[0] - c[0], d[1] - c[1])
        d1 = math.hypot(*v1) or 1.0
        d2 = math.hypot(*v2) or 1.0
        cs = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (d1 * d2)))
        if math.degrees(math.acos(cs)) < min_deg:
            return True
    return False


# A BUND RUNS ON, OR IT TURNS FOR A REASON - IT DOES NOT STEP SIDEWAYS AND CARRY ON (GM 2026-08-18,
# on Inashiro: "instead of just continuing on and meeting at the four way intersection ... it just
# goes sharply to the left before going down"). The aze is puddled mud re-plastered every spring
# (azenuri) and its bill is its LENGTH, with the corners the part that slumps hardest; a jog buys two
# right-angle corners and the run between them in exchange for ground that sits at the same level,
# floods from the same offtake and is reachable from either basin. `research/fields.md` is equally
# firm the other way - the organic waver is period-correct and an odd-shaped parcel is honest - so
# the shape this refuses is narrow and specific: a run of wall, a short hop SIDEWAYS, and the same
# run resuming in the SAME DIRECTION a few feet over.
#
# THESE ARE THE PLACER'S NUMBERS, one notch stricter on every axis than the rule they answer to, the
# way `_WELD_MIN_APEX` sits above `_GATE_MIN_APEX`: the rule fires at a 3 ft offset with 8 ft runs
# and a 25 ft link, so a weld is refused here at 2 ft with 6 ft runs and a 30 ft link. Same
# measurement, stricter threshold - never a second measurement bolted alongside it.
#
# THE RULE IS NOT IN THE GATE YET, and that is the open half of this work rather than a decision:
# the engine still leaves 16-33 steps on each scripted hamlet, so a gate check would fail the pool
# on day one. `tools/jogs.py` reports them on demand meanwhile, and `future-work.md` "paddy bunds
# still step sideways" carries the residual counts, the two reverted implementation attempts with
# what each broke, and the sketch - of which moving this rule into `check_village` is the last step.
_JOG_OFF_FT = 2.0
_JOG_RUN_FT = 6.0
_JOG_LINK_FT = 30.0
_JOG_PARALLEL_DEG = 20.0
# AND THE HOP MUST BE ACROSS THE WALL, NOT ALONG IT. Without this the test fires on a gently CURVING
# bund: sample a curve into ~30 px segments and every three of them read as a run, a link and a run
# resuming near-parallel, with a perpendicular offset of a few feet purely from the bend. Measured
# 2026-08-18 on Kuwabata, whose paddies are drawn as long curved parcels - 57 reported steps on 43
# plot rings, every one of them a smooth bend, against 6 for the same map when the turn is tested.
# A real step turns hard at both ends of the hop; 55 deg is well clear of the ~10-20 deg a sampled
# curve turns and well under the 90 deg a rectangular tab turns, so it separates them without
# needing to be tuned. (The two turns are opposite in sign by construction once the runs are
# required to be near-parallel, so only the magnitude is tested.)
_JOG_CORNER_DEG = 55.0


def jog_steps(ring: Poly, g: float) -> int:
    """How many times `ring` steps sideways and carries on parallel to itself."""
    return len(jog_vertices(ring, g))


def jog_vertices(ring: Poly, g: float) -> list[tuple[Pt, Pt]]:
    """The two vertices of each sideways step in `ring` - the ends of the hop, in ring order.

    `g` is the engine's grain (`2 / ftpx`), so px-per-foot is `g / 2` - the same unit conversion
    `close_seams` uses for the 3 ft doubled-bund floor, and the one place to get it wrong.

    HEADINGS ARE COMPARED OVER THE FULL CIRCLE, not modulo 180 deg. Modulo 180 the test also matches
    a plain thin rectangle (long side, short end, long side coming back), so every narrow basin the
    fabric legitimately carries would report a step on its own end wall - measured 2026-08-18 on the
    shipped Inashiro, 78 hits against 28 for the directed test, the extra 50 all end walls."""
    ring = dedup_ring(ring, 0.5)
    n = len(ring)
    if n < 5:
        return []  # a quad has no room for a run, a hop and the run resuming
    px = g / 2.0
    run = _JOG_RUN_FT * px
    link = _JOG_LINK_FT * px
    off = _JOG_OFF_FT * px
    out: list[tuple[Pt, Pt]] = []
    for i in range(n):
        a, b, c, d = ring[i], ring[(i + 1) % n], ring[(i + 2) % n], ring[(i + 3) % n]
        e1 = (b[0] - a[0], b[1] - a[1])
        e2 = (c[0] - b[0], c[1] - b[1])
        e3 = (d[0] - c[0], d[1] - c[1])
        l1 = math.hypot(*e1)
        l2 = math.hypot(*e2)
        l3 = math.hypot(*e3)
        if l1 < run or l3 < run or not (0.0 < l2 <= link):
            continue
        h1 = math.degrees(math.atan2(e1[1], e1[0]))
        h3 = math.degrees(math.atan2(e3[1], e3[0]))
        if abs((h3 - h1 + 180.0) % 360.0 - 180.0) > _JOG_PARALLEL_DEG:
            continue
        h2 = math.degrees(math.atan2(e2[1], e2[0]))
        if abs((h2 - h1 + 180.0) % 360.0 - 180.0) < _JOG_CORNER_DEG or abs((h3 - h2 + 180.0) % 360.0 - 180.0) < _JOG_CORNER_DEG:
            continue
        if abs(-(e1[1] / l1) * e2[0] + (e1[0] / l1) * e2[1]) >= off:
            out.append((b, c))
    return out


def pointed_ring(poly: Poly, min_deg: float = 25.0) -> bool:
    """Does this ring taper to a POINT - an interior angle sharper than `min_deg`?

    The flooded-wedge discriminator (known-open ledger 2026-08-16): at a fan seam the closing
    rank's converging sub-columns produce slivers that taper to needle apexes, and one carrying
    the FLOODED tint reads as a tiny triangular POND at fit zoom (conspicuous on Sawada, whose
    brief is "no pond"). A legitimate flooded hem strip is a bunded rectangle - interior angles
    near 90 deg - so the apex angle separates the two cleanly (measured across the pool: the
    seam wedges run 7-23 deg, the hem strips 45+). ONE predicate, two calibrated thresholds:
    the carve demotes the tint at 25 deg (generous - a green sliver among green slivers costs
    nothing), the gate (`flooded_plots_read_as_basins`) fires at 15 deg (only the unmistakable
    needles), so a borderline plot the carve demotes cannot false-fire the check - the same
    placer-stricter-than-gate calibration as the supply-bank margins."""
    n = len(poly)
    for i in range(n):
        a, v, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        v1 = (a[0] - v[0], a[1] - v[1])
        v2 = (c[0] - v[0], c[1] - v[1])
        d1 = math.hypot(*v1) or 1.0
        d2 = math.hypot(*v2) or 1.0
        cosv = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (d1 * d2)))
        if math.degrees(math.acos(cosv)) < min_deg:
            return True
    return False


def dedup_ring(pts: Poly, eps: float = 1.0) -> Poly:
    """Collapse consecutive vertices closer than `eps` (the closing pair included).

    The envelope trim clamps runs of vertices onto the collector line, and where the cut meets
    the old boundary it deposits near-duplicate points with back-and-forth reversals (~12 points
    in a ~5 px span on Kashikawa, merged-roll review 2026-08-16). Invisible at 1 ft/px, but a
    consumer of the ring - an area, an edge normal, a self-intersection test - can trip on the
    micro-zigzag, so the duplicates are merged the same way the bowtie pass merges collapsed
    plot vertices."""
    out = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > eps]
    while len(out) > 1 and math.dist(out[0], out[-1]) <= eps:
        out.pop()
    return out
