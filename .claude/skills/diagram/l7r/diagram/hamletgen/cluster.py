"""STAGE 4a: seating the settlement on the margin the water leaves.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from l7r.diagram.settlement import point_in_poly, seg_closest, seg_dist, seg_intersect
from l7r.diagram.sitegen.geom import centroid, unit

from .consts import BUNDLE_PITCH, Poly, Pt
from .plan import SitePlan

# ---- STAGE 4: seating the settlement, and its ways ----------------------------------------------


def below_drain(pt: Pt, drain: Poly, dx: float, dy: float, band: float = 150.0) -> bool:
    """Is `pt` on the WET side of the drain collector, within a toe band of it?

    The same question `dwellings_above_field_drain` asks of every dwelling, asked before the
    dwellings exist. Reading the check's own predicate rather than approximating it with "downhill
    of the field centroid" is the point: an aggregate cannot stand in for a distributed thing, and
    the drain is a LINE across the low side, not a point."""
    near = min(range(len(drain) - 1), key=lambda i: seg_dist(pt[0], pt[1], drain[i], drain[i + 1]))
    d = seg_dist(pt[0], pt[1], drain[near], drain[near + 1])
    proj = seg_closest(pt[0], pt[1], drain[near], drain[near + 1])
    return (pt[0] - proj[0]) * dx + (pt[1] - proj[1]) * dy > 18.0 and d <= band


def back_fouled(anchor: Pt, out: Pt, dep: float, dry_plots: Sequence[Poly], reach: float = 2.6, samples: int = 7) -> float:
    """What fraction of the ground BEHIND a candidate margin is already cropland.

    Samples a fan of points running out from the anchor along its outward normal, over the depth the
    cluster plus its windbreak will occupy. Returns 0.0 for a clear back and 1.0 for one entirely
    under the hem."""
    if not dry_plots:
        return 0.0
    ax, ay = -out[1], out[0]
    hit = 0
    total = 0
    for i in range(samples):
        t = (i + 0.5) / samples
        for lat in (-0.5, 0.0, 0.5):
            px = anchor[0] + out[0] * dep * reach * t + ax * dep * lat
            py = anchor[1] + out[1] * dep * reach * t + ay * dep * lat
            total += 1
            hit += any(point_in_poly(px, py, list(poly)) for poly in dry_plots)
    return hit / total


def seat_cluster(plan: SitePlan, dry_plots: Sequence[Poly] = (), drain: Poly | None = None, toe: Poly | None = None) -> dict[str, Any]:
    """WHERE THE HOUSES GO - the one derivation that decides how the whole map reads.

    背山面水, "back to the hill, face the water": a farming settlement stands with its back to the
    high, cold, windward side and its face to the field and its water. That is not decoration, it is
    the reason the windbreak grove has a side to be on, and it is what Ikegami's own docstring cites.
    So the cluster is seated on the field-envelope margin whose OUTWARD NORMAL best points into the
    wind, tie-broken toward the UPSLOPE end - which is also where the gate needs the dwellings to be
    (`dwellings_above_field_drain`: the ground below the drainage line is the wettest in the valley
    and is not building ground).

    Scoring every margin point of the DRAWN envelope, rather than picking a compass corner, is what
    makes this survive a field that came out a different shape: the seat follows the fan.

    Returns the seat frame - a center, an ALONG-the-margin unit, an AWAY-from-the-field unit, and
    the band's half-extents - which the lanes, the house seeds, the connector and the windbreak all
    work in, so every one of them lands correctly at any fall direction."""
    env = plan.envelope
    cen = centroid(env)
    dx, dy = plan.fall
    wx, wy = plan.wind
    # A band sized from the household count x the ground a homestead ACTUALLY takes.
    #
    # THE PITCH IS THE WHOLE THING, and getting it wrong is silent. `roll_village` sizes its band at
    # a 56 px pitch per household, which is the FARMHOUSE - but the to-scale tiers do not place a
    # farmhouse, they place a BUNDLE: house (46 x 28 ft) plus its threshing yard below and its
    # dooryard garden beside, ~71 x 57 ft of reserved ground, and the placer keeps bundles apart by
    # circumscribed circles rather than real footprints, which costs up to another ~2x in spacing
    # (the engine's documented collision-circle debt). 56 px per household therefore asks a band to
    # hold about three times what fits in it.
    #
    # The symptom is NOT a shortfall, which is what makes it worth writing down: the retry loop
    # widens the band until the houses do fit, so the count comes out right and the cluster ends up
    # packed absolutely solid. Then the wells have nowhere to go - 702 candidate seats offered,
    # every one refused, `open_seat` finding nothing anywhere in the cluster - and the map fails
    # `settlement_has_wells` for a reason that looks nothing like its cause. Sizing the band from
    # the bundle leaves the courtyards a well can stand in.
    dep = max(112.0, min(math.sqrt(plan.spec.households * (BUNDLE_PITCH**2) / (3.0 * math.pi)), 300.0))
    lat = max(240.0, min(plan.spec.households * (BUNDLE_PITCH**2) / (math.pi * dep), 1100.0))

    best: tuple[float, Pt, Pt] | None = None
    n = len(env)
    for i in range(n):
        ax, ay = env[i]
        bx, by = env[(i + 1) % n]
        mid = ((ax + bx) / 2.0, (ay + by) / 2.0)
        # THE EDGE'S OWN NORMAL, turned to face away from the field - not the ray from the field's
        # middle. A comb fan is NOT CONVEX: it has concave shoulders where the carve stops short,
        # and on those edges "away from the centroid" points straight back INTO the rice. Seeding a
        # cluster there put ten households on the paddy, where every candidate footprint was refused
        # by the crop keep-out and only four houses of a declared ten ever landed (seed 11). The
        # centroid ray is a plausible-looking approximation of an outward normal that is simply
        # wrong for the one shape this generator always draws.
        nx, ny = unit(-(by - ay), bx - ax)
        if (nx * (mid[0] - cen[0]) + ny * (mid[1] - cen[1])) < 0:
            nx, ny = -nx, -ny  # flip to the outward side (winding-independent)
        rel = ((mid[0] - cen[0]), (mid[1] - cen[1]))
        # ...and belt-and-braces: the BAND ITSELF must stand on open ground. An edge normal can
        # still graze a lobe of the fan a little further along, and a check is cheaper than a theory.
        if any(point_in_poly(mid[0] + nx * d - ny * lat * t, mid[1] + ny * d + nx * lat * t, env) for d in (dep * 0.5, dep + 34.0, dep * 2.0) for t in (-0.6, 0.0, 0.6)):
            continue
        # HARD 1: never below the DRAIN. The ground under the drainage line is the wettest in the
        # valley - reed marsh, the tameike, the low reclaimed paddy - and it is not building ground
        # (`dwellings_above_field_drain` says exactly this). Excluded rather than scored down: a
        # soft penalty lets a strong enough wind score pull the settlement into the bog.
        #
        # Measured against the DRAIN POLYLINE, not against the field's middle. "Above the middle"
        # was tried first and was much too strict - it is the dry HEM that hems the upslope margin,
        # so banning the downslope half leaves only the hem to build on, and the whole cohort came
        # back with its lanes and its grove standing in the hatake plots. The wet toe is a thin band
        # along one edge; the buildable ground is the two flanks, which is where Ikegami's cluster
        # sits and where this now puts it.
        if drain is not None and below_drain(mid, drain, dx, dy):
            continue
        # HARD 2: there must be clear ground BEHIND the margin. The settlement is a band and its
        # windbreak is a belt behind that - together most of a cluster's depth again - so a margin
        # is only usable if the ground it backs onto is free of crop. Testing the anchor POINT is
        # not enough (that was the first attempt): a point can stand clear of the hem while the belt
        # that goes 250 px behind it lands squarely in the plots.
        if back_fouled(mid, (nx, ny), dep, dry_plots) > 0.30:
            continue
        # HARD 3: the band has to FIT ON THE CANVAS. A margin near the canvas edge seats its band
        # center outside it - and `_fits` refuses every candidate beyond `s.bound`, so the cluster
        # simply does not get built: seed 106 seated 7 farmhouses of a declared 15, with the band's
        # center 56 px off the east edge. The map is not wrong, the seat is; another margin will do.
        seat_c = (mid[0] + nx * (dep + 12.0), mid[1] + ny * (dep + 12.0))
        if not (lat * 0.5 <= seat_c[0] <= plan.W - lat * 0.5 and lat * 0.5 <= seat_c[1] <= plan.H - lat * 0.5):
            continue
        # HARD 4: THE CLUSTER IS NOT BUILT ON THE WET TOE (GM 2026-08-12). `hinterland` lays reed
        # marsh across everything below the crop's low point, and on a crescent cluster hugging the
        # fan's toe the seat landed INSIDE that band - so the settlement's own lanes started in the
        # marsh and no amount of routing could save them (3 of 36 cohort maps). No reeds are drawn
        # on the houses, because the scatter skips the settlement halo, but the ground is still
        # marsh and the map says so. This is the same instinct as HARD 1 one step further out: you
        # do not build in the bog, and you do not build where the bog is either.
        if toe and (point_in_poly(seat_c[0], seat_c[1], toe) or point_in_poly(mid[0], mid[1], toe)):
            continue
        # 1.0 x facing the wind (the back), 0.8 x being upslope. Both express the same siting
        # instinct from two directions, and weighting the wind slightly higher keeps the windbreak
        # unambiguously behind the houses even on a map whose fall and wind nearly oppose.
        score = 1.0 * (nx * wx + ny * wy) - 0.8 * unit(*rel)[0] * dx - 0.8 * unit(*rel)[1] * dy
        # ...MINUS the dry hem. The upslope margin is contested ground: the comb's dry (hatake)
        # plots hem the high side along the supply canal, and they are cropland - a settlement
        # seated on top of them puts its windbreak's canopy in the crop (`groves_clear_of_dry_plots`)
        # and its farmsteads on the plots (`structures_clear_of_dry_plots`). So a margin that is
        # already hemmed scores down, in proportion to how close the hem is, and the seat slides
        # around the field to the free shoulder. Nothing here says WHICH shoulder - the geometry
        # does, which is why this works on a fan that came out a different shape.
        if dry_plots:
            hem = min(min(seg_dist(mid[0], mid[1], p[i], p[(i + 1) % len(p)]) for i in range(len(p))) for p in dry_plots)
            score -= 1.6 * max(0.0, 1.0 - hem / (2.0 * dep))
            score -= 2.5 * back_fouled(mid, (nx, ny), dep, dry_plots)
        if best is None or score > best[0]:
            best = (score, mid, (nx, ny))
    if best is None:  # pragma: no cover - a fan always leaves one buildable flank; belt and braces
        raise ValueError("no field margin is clear of the drain and the dry hem - the fan has no buildable flank")
    _, anchor, out = best
    along = (-out[1], out[0])
    # THE BAND'S NEAR EDGE HUGS THE FIELD. The standoff is the front row's own depth and no more:
    # `field_ringed` wants at least five farmhouses within 165 px of the field outline, and every
    # pixel of standoff comes off that count twice over, because the band is seeded across its whole
    # depth rather than packed against its near face. At 34 px of standoff three cohort maps rang
    # their field with four houses; at 12 the same maps ring it comfortably, and the front row still
    # fronts the paddy across its lane rather than standing in the rice.
    cx = anchor[0] + out[0] * (dep + 12.0)
    cy = anchor[1] + out[1] * (dep + 12.0)
    return {"cx": cx, "cy": cy, "along": along, "out": out, "lat": lat, "dep": dep, "anchor": anchor}


def _arm_hit(a: Poly, b: Poly) -> Pt | None:
    """The first PROPER mid-run crossing point of two polylines - a touch at a segment
    endpoint is a JUNCTION, not a crossing, and returns nothing. Returning the POINT rather
    than a bool matters: raw skeletons may cross by design (a stem poked through its bar, the
    'cross' layout's crossbar over its spine), so "the raw pair crosses somewhere" cannot
    license a clipped crossing ANYWHERE - Kashikawa's two clipped arms X-ed 87 px out in open
    ground while their raw junction sat at the hub, and the existence test waved it through
    (2026-08-16). A clipped crossing is designed only where the raw one is."""
    for i in range(len(a) - 1):
        for j in range(len(b) - 1):
            _h = seg_intersect(a[i], a[i + 1], b[j], b[j + 1])
            if _h is not None and all(math.dist(_h, q) > 2.0 for q in (a[i], a[i + 1], b[j], b[j + 1])):
                return _h
    return None


def _arm_crossing_accidental(arm: Poly, raw: Poly, kept: list[tuple[Poly, Poly]]) -> bool:
    """AN ARM MAY NOT CROSS A SIBLING ANYWHERE THE LAYOUT DOES NOT (settlement-review, Sawada
    2026-08-16): the clip pipeline bends each arm independently, and two of a Y's arms came back
    CROSSING mid-run in open ground, near-superimposed for ~250 ft. A clipped crossing is designed
    only where the RAW pair crosses within ~40 px of it - existence alone is not enough, since a
    raw stem poked through its bar "crosses" at the hub while the clipped X sat 87 px away."""
    for k_arm, k_raw in kept:
        _h = _arm_hit(arm, k_arm)
        if _h is None:
            continue
        _hr = _arm_hit(raw, k_raw)
        if _hr is None or math.dist(_h, _hr) > 40.0:
            return True
    return False


def _fork_spur(spur_pts: Poly, kept: list[tuple[Poly, Poly]]) -> Poly:
    """A FIELD SPUR BRANCHES OFF THE NETWORK - it does not cross it (settlement-review, Sawada
    2026-08-16: the spur left the cluster's middle on the far side of a Y arm and ran an X over
    it, where a real farm path FORKS from the lane it serves). If the run crosses a drawn arm,
    the spur starts AT the crossing: the shared point becomes the fork. BOUNDED pass count: with
    float hits a crossing can re-surface epsilon-shifted forever (the unbounded while hung a
    regen at 600s); a spur meets at most a handful of arms, so eight passes is generous and
    termination is structural, not numeric. The progress guard matters too: after a truncation
    the new start lies ON the arm, so the same intersection comes straight back on the next pass
    - a hit at the current start is the fork already made, not a crossing left to cure."""
    for _pass in range(8):
        _cut = False
        if len(spur_pts) < 2:
            break
        for _ka, _kr in kept:
            for _si in range(len(spur_pts) - 1):
                for _sj in range(len(_ka) - 1):
                    _hit = seg_intersect(spur_pts[_si], spur_pts[_si + 1], _ka[_sj], _ka[_sj + 1])
                    if _hit is not None and math.dist(_hit, spur_pts[-1]) > 14.0 and math.dist(_hit, spur_pts[_si]) > 1.0:
                        spur_pts = [_hit, *spur_pts[_si + 1 :]]
                        _cut = True
                        break
                if _cut:
                    break
            if _cut:
                break
        if not _cut:
            break
    return spur_pts
