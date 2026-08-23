"""STAGE 4b: the lanes, the connector track, and what makes a path legal.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Sequence

from l7r.diagram.settlement import Settlement, point_in_poly, rot_rect, seg_closest, seg_dist, seg_intersect, segments_cross, skeleton_layout, web_cuts
from l7r.diagram.sitegen.geom import centroid, crop_polys, crosses_disc, crosses_poly, pull_clear, unit

from .cluster import _arm_crossing_accidental, _fork_spur, seat_cluster
from .consts import (
    BUNDLE_PITCH,
    CLUSTER_SPAN_FACTOR,
    FOOTPATH_FABRIC_GAP,
    LANE_CLEARANCE,
    MIN_WEB_GAP,
    SPUR_SETBACK,
    WEB_CLEARANCE,
    WEB_FABRIC_GAP,
    WEB_HARD_GAP,
    WEB_REACH_FT,
    WEB_SHADOW_FT,
    WIND_VECTORS,
    Poly,
    Pt,
)
from .plan import SitePlan


class _margin_frame:  # noqa: N801 - used as a callable coordinate map, not as a type
    """OUTLINE COORDINATES for the stretch of field margin this cluster fronts.

    `f(arc, standoff)` maps a point given as (distance walked along the field edge, distance out
    from it) to screen. It is the same walk `front_row` makes - the outline vertices within the
    cluster's lateral reach, ordered along the margin, each offset outward on the local normal - and
    it exists for the same reason: the margin CURVES, so anything meant to run parallel to the field
    has to be built on the edge itself rather than ruled straight across it.

    Read `.arc` for the total length of that stretch, which is the domain the web is laid over."""

    def __init__(self, plan: SitePlan, span: float, near: Sequence[Pt] = ()) -> None:
        env, seat = plan.envelope, plan.seat
        ax, ay = seat["along"]
        cen = centroid(env)
        # ONE CONTIGUOUS RUN OF THE OUTLINE, WALKED FROM THE CLUSTER OUTWARD - not a filter.
        #
        # The envelope is a closed RING, so any test applied vertex-by-vertex admits the far side of
        # the field as readily as the near one, and the arc then snakes down one flank of the fan,
        # round the end and back up the other: 3,060 ft of "margin" for an 808 ft cluster, which
        # over-generated laterals three to one and laid them where no house stands. A half-plane
        # test off the seat's outward normal fixes that and breaks something else - a CRESCENT
        # cluster wraps around the field, its far arm sits where the normal points elsewhere, and it
        # was cut out of the frame entirely, so those houses could not be reached at any price.
        #
        # Walking instead of filtering settles both. Start at the outline vertex nearest the seat and
        # step each way while the outline is still near the settlement: the run is contiguous by
        # construction, so it can never jump the field, and it follows a crescent round for exactly
        # as far as the crescent goes. The walk looks a few vertices AHEAD before giving up, because
        # a crescent's two arms are separated by margin that no house stands near, and stopping at
        # the first far vertex stops between the arms. `near` is the placed house centers - measured,
        # not predicted, because by the time the web is laid they exist.
        anchor = seat["anchor"]
        limit = max(span, BUNDLE_PITCH)

        def close_enough(q: Pt) -> bool:
            if near:
                return min(math.dist(q, h) for h in near) <= limit
            return bool(abs((q[0] - anchor[0]) * ax + (q[1] - anchor[1]) * ay) <= span)

        n_env = len(env)
        look = 12

        def worth_continuing(i: int, step: int) -> bool:
            return any(close_enough(env[(i + step * k) % n_env]) for k in range(1, look + 1))

        # THE WALK MAY NOT LAP THE FIELD. Bounded by arc as well as by vertex count: on a compact
        # outline the look-ahead can carry the walk right round the ring and back to where it began,
        # and a frame that laps has no single answer for `project` - two stretches of it sit on top
        # of each other, so a point maps to whichever the scan met first. Half the ring is the most
        # margin any one cluster can honestly front.
        ring = sum(math.dist(env[i], env[(i + 1) % n_env]) for i in range(n_env))
        cap = ring * 0.5
        start = min(range(n_env), key=lambda i: math.dist(env[i], (seat["cx"], seat["cy"])))
        walked = 0.0
        lo = start
        while (start - lo) < n_env - 1 and walked < cap and worth_continuing(lo, -1):
            walked += math.dist(env[(lo - 1) % n_env], env[lo % n_env])
            lo -= 1
        hi = start
        while (hi - start) < n_env - 1 and walked < cap and worth_continuing(hi, +1):
            walked += math.dist(env[hi % n_env], env[(hi + 1) % n_env])
            hi += 1
        pts = [env[i % n_env] for i in range(lo, hi + 1)]
        if len(pts) < 2:  # pragma: no cover - a band always spans several outline vertices
            pts = [(seat["cx"], seat["cy"]), (seat["cx"] + ax, seat["cy"] + ay)]
        self.pts = pts
        self.cum = [0.0]
        for i in range(len(pts) - 1):
            self.cum.append(self.cum[-1] + math.dist(pts[i], pts[i + 1]))
        self.arc = self.cum[-1]
        # The outward normal at each vertex, averaged over the two edges meeting there and oriented
        # AWAY from the field's centroid - the settlement is outside the crop, and a standoff that
        # pointed inward would lay every web lane in the rice.
        self.nrm: list[Pt] = []
        for i, p in enumerate(pts):
            nx, ny = 0.0, 0.0
            for a, b in ((pts[max(0, i - 1)], p), (p, pts[min(len(pts) - 1, i + 1)])):
                if a != b:
                    ex, ey = unit(-(b[1] - a[1]), b[0] - a[0])
                    nx, ny = nx + ex, ny + ey
            nx, ny = unit(nx, ny) if (nx or ny) else (1.0, 0.0)
            if nx * (p[0] - cen[0]) + ny * (p[1] - cen[1]) < 0:
                nx, ny = -nx, -ny
            self.nrm.append((nx, ny))

    def project(self, p: Pt) -> tuple[float, float]:
        """The inverse of `__call__`: a screen point as (arc along the margin, standoff out from it).

        By nearest sample on the centerline rather than by solving, because the margin is a
        polyline with corners and the nearest-point problem there has no closed form worth writing.
        The samples are one every 10 ft, which is a tenth of the reach anything is measured against."""
        n = max(2, int(self.arc / 10.0))
        best = (0.0, 0.0, float("inf"))
        for i in range(n + 1):
            a = self.arc * i / n
            q = self(a, 0.0)
            d = math.dist(p, q)
            if d < best[2]:
                best = (a, d, d)
        return (best[0], best[1])

    def __call__(self, arc: float, standoff: float) -> Pt:
        t = min(max(arc, 0.0), self.arc)
        i = max(0, min(len(self.pts) - 2, next((k for k in range(len(self.cum) - 1) if self.cum[k + 1] >= t), len(self.pts) - 2)))
        run = self.cum[i + 1] - self.cum[i]
        u = 0.0 if run <= 0 else (t - self.cum[i]) / run
        px = self.pts[i][0] + (self.pts[i + 1][0] - self.pts[i][0]) * u
        py = self.pts[i][1] + (self.pts[i + 1][1] - self.pts[i][1]) * u
        nx = self.nrm[i][0] + (self.nrm[i + 1][0] - self.nrm[i][0]) * u
        ny = self.nrm[i][1] + (self.nrm[i + 1][1] - self.nrm[i][1]) * u
        nx, ny = unit(nx, ny) if (nx or ny) else self.nrm[i]
        return (px + nx * standoff, py + ny * standoff)


def _homestead_polys(s: Settlement) -> list[tuple[Poly, Pt | None, str]]:
    """Every drawn thing a homestead puts on the ground, as (polygon, the house it belongs to).

    The OWNER matters for one job only, and it is the job that needs it most: a footpath to an
    outlying steading has to be allowed to leave that steading's own yard. Without the owner the
    path starts at the door, immediately meets its own threshing yard, and is clipped to nothing -
    which is how eight houses stayed unreachable while a path to each was being drawn and thrown
    away. `of` on a yard/garden/shed records its house's center, so the association is already in
    the manifest and does not have to be re-derived geometrically.

    Houses are rotated rects and are read as their real corners (x, y ARE the center here, the same
    convention `rect_corners` uses in the gate); the area features already record an outline."""
    out: list[tuple[Poly, Pt | None, str]] = []
    for h in s.M.get("houses", []):
        c = (float(h["x"]), float(h["y"]))
        out.append((rot_rect(c[0], c[1], float(h["w"]), float(h["h"]), float(h.get("rot", 0.0))), c, "houses"))
    for key in ("threshing_yards", "gardens"):
        for rec in s.M.get(key, []):
            own = rec.get("of")
            owner = (float(own[0]), float(own[1])) if own else None
            # BOTH EXTENTS, because they are not the same shape and the gate reads the wider one. A
            # garden records a `poly` (the bed outline) AND a rect, and the rect runs a couple of
            # feet proud of the poly on a side or two. Clearing only the poly left about eight inches
            # between a web lane and the rect - and the overlap matrix sizes EVERY lane at 6 ft wide
            # whatever its own record says, so eight inches was an overlap. That was 7 of 24 cohort
            # seeds, all of them `lanes` vs `gardens`.
            if rec.get("poly"):
                out.append(([(float(a), float(b)) for a, b in rec["poly"]], owner, key))
            if rec.get("w"):
                out.append((rot_rect(float(rec["x"]), float(rec["y"]), float(rec["w"]), float(rec["h"]), float(rec.get("rot", 0.0))), owner, key))
    # PER-HOUSE GROVES ARE FABRIC TOO (feature 126). A yashikirin belongs to its farmstead and is
    # planted with it, so a lane may no more be drawn through one than through the house - which is
    # what `groves_clear_of_lanes` says. It was missing from this list because it could not matter
    # while the lanes were laid FIRST and the groves grew around them; with the lanes drawn last,
    # every non-nucleated map cut treads through its own shelter belts.
    for rec in s.M.get("groves", []):
        if rec.get("poly"):
            out.append(([(float(a2), float(b2)) for a2, b2 in rec["poly"]], None, "groves"))
    for key in ("village_groves", "commons"):
        out.extend(([(float(a), float(b)) for a, b in rec["poly"]], None, key) for rec in s.M.get(key, []) if rec.get("poly"))
    for w in s.M.get("wells", []):
        # THE DRAWN radius, not the recorded one. A wellhead records `r` (the shaft) and `vr` (the
        # curb and apron actually inked), and `vr` is the bigger of the two - built from `r` alone
        # the obstacle was a diamond inside the glyph, and a web lane passed 13 ft from the center
        # with the matrix quite rightly calling it an overlap. Octagon rather than diamond for the
        # same reason: a four-point ring inscribed in a circle understates it by 30%.
        r = max(float(w.get("r", 8.0)), float(w.get("vr", 0.0)))
        out.append(([(float(w["x"]) + r * math.cos(math.pi * k / 4), float(w["y"]) + r * math.sin(math.pi * k / 4)) for k in range(8)], None, "wells"))
    for key in ("farm_sheds", "byres"):
        for r in s.M.get(key, []):
            own = r.get("of")
            out.append((rot_rect(float(r["x"]), float(r["y"]), float(r["w"]), float(r["h"]), float(r.get("rot", 0.0))), (float(own[0]), float(own[1])) if own else None, key))
    return out


def _lay_skeleton(s: Settlement, plan: SitePlan, frame: _margin_frame, arcs: Sequence[float], stands: Sequence[float]) -> list[tuple[Poly, Poly]]:
    """The cluster's internal SKELETON, laid AFTER the houses and fitted to where they went.

    THIS USED TO RUN BEFORE THE HOUSES, and moving it is feature 126's whole point. The GM asked
    whether pre-laying lanes reflects how they form, and it does not: a lane between farmsteads is
    trodden by households already living there. The project had reached that conclusion once already
    for the lane WEB - "an alley IS the residual gap between two plots ... not a corridor set aside
    in advance" - and this is the half that was still laid first.

    It was also measurably wrong. The skeleton was sized on the SEAT BAND while the houses spread
    wider than the band, so it could not be guaranteed to reach them; that mismatch is the root of
    the `farmhouses_reach_a_way` defect that survived seventeen recorded attempts. Fitted to the
    houses' own arc extent instead, the question does not arise - the arms span the settlement that
    actually exists rather than the one the band predicted.

    The frame, arcs and stands are the caller's, already measured off the placed houses, so the
    skeleton and the web share one coordinate domain and cannot disagree about where the cluster is.
    Returns the kept arms, for the web to treat as existing network."""
    if len(arcs) < 2:
        return []
    arc0 = (min(arcs) + max(arcs)) / 2.0

    stand0 = sum(stands) / len(stands)
    # SIZED FROM THE HOUSES, not from `seat["lat"]`/`seat["dep"]`. Half-extents, because
    # `skeleton_layout` takes half-widths, and floored at one bundle pitch so a tight cluster still
    # gets a spine with somewhere to run.
    lat = max((max(arcs) - min(arcs)) / 2.0, BUNDLE_PITCH * 0.5)
    dep = max((max(stands) - min(stands)) / 2.0, BUNDLE_PITCH * 0.5)
    layout = skeleton_layout(plan.lane_skeleton, 0.0, 0.0, lat, dep)

    def _on_margin(p: Pt) -> Pt:
        # local +x runs along the band, local +y toward the field (so OUT of the frame is -y).
        q = frame(arc0 + p[0], stand0 - p[1])
        return (float(q[0]), float(q[1]))

    raw_arms = [[_on_margin((float(p[0]), float(p[1]))) for p in lane_pts] for lane_pts in layout["lanes"]]
    crops = crop_polys(s)
    # what is already standing: houses, yards, gardens, sheds - the arm must go round all of it
    fabric = [poly for poly, _owner, _kind in _homestead_polys(s)]
    toe_now = s.toe_band() or None
    wet_now = [[(float(a), float(b)) for a, b in m["poly"]] for m in s.M.get("marshes", []) if m.get("role") != "defense" and m.get("poly")]
    drawn_water = [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for rec in s.M.get("drawn_channels", []) for a, b in zip(rec["pts"], rec["pts"][1:], strict=False)]
    kept: list[tuple[Poly, Poly]] = []
    for ai in range(len(raw_arms)):
        # Clipped exactly as before the move: off the crop, off the wet toe and every drawn marsh,
        # and off the water - an internal arm serves the houses and has no business crossing a ditch
        # (the spur and the connector are the ways that LEAVE, and they meet water squarely).
        # THE OBLIGATION INVERTED WITH THE ORDER, and this is the half that was missing (feature
        # 126). While the skeleton was laid FIRST, a lane was a no-build corridor and the HOUSES
        # avoided it. Laid last, nothing was stopping the arm from being drawn straight through a
        # farmstead - and nothing was: the in-gate ratchet went to 0 of 4, failing
        # `houses_clear_of_lanes`, `houses_off_corridors` and `features_do_not_overlap` on seeds
        # 41, 42 and 44. Reordering the stages is not enough on its own; every rule that pointed one
        # way across that boundary has to be turned around to match.
        #
        # `_homestead_polys` is the same fabric the web threads between (see `stage_web`), so the
        # skeleton and the web now agree about what is already standing.
        # TWO CLEARANCES, BECAUSE THEY ARE TWO DIFFERENT RULES.
        #
        # Crop, water and marsh want the full 20 px: a track keeps clear of standing rice and does
        # not skim a ditch. The FABRIC does not, and holding it to the same figure is what made the
        # first version of this pathological. A 20 px margin demands a 40 px clear corridor between
        # two steadings, which a packed cluster does not have - so instead of threading the gap the
        # arm was clipped away entirely, the cluster went unserved, and `_serve_stragglers` spent its
        # four passes routing rescue footpaths that mostly failed and were retried. Measured on
        # THIS DID NOT FIX THE SEED-25 COST, and the honest note matters more than the tidy one:
        # measured before and after, `stage_web` stayed at ~299 s with `_route` called 817 times
        # either way. So the arms were NOT being clipped out of existence by the fabric margin, and
        # whatever drives the straggler routing lies elsewhere. The split is kept because it is
        # right on its own terms, not because it bought anything.
        #
        # FABRIC_GAP is what these lanes actually are. The sources describe the lateral ones as
        # "colonized as semi-private space by the adjoining house" and barely more than the gap
        # between two walls - so the arm needs its own half-width and a little air, not a highway
        # verge. This is the same `WEB_FABRIC_GAP` the lane web already threads by, so the skeleton
        # and the web now agree about how close a lane may pass a wall.
        arm = clip_to_clear(raw_arms[ai], [list(plan.envelope), *crops, *([toe_now] if toe_now else []), *wet_now], 20.0, lines=list(plan.watercourses) + drawn_water)
        # ROUTE ROUND THE FABRIC, DO NOT CLIP THROUGH IT (feature 126, after review).
        #
        # Clipping was the first version and it deletes the form. An arm that crosses a packed
        # cluster meets a steading, gets cut, and what survives is whichever end happened to fall in
        # open ground - so a declared `Y` shipped ONE arm of three on Sawada and Mizuguchi, a `T`
        # shipped two arms that never meet on Kashikawa, and Inashiro's spine covered the middle
        # third of a crescent with 60% of its planned run trimmed away. Three independent
        # settlement-reviews found the same thing from three different maps.
        #
        # A trodden way does not stop at a wall, it goes ROUND it, and `_route` is the same Dijkstra
        # the lane web already uses for exactly this. The clip stays as the fallback: where no route
        # exists the honest outcome is still a shortened arm rather than a lane through a house.
        if len(arm) >= 2:
            routed = _route(arm[0], arm[-1], [list(plan.envelope), *crops, *fabric, *([toe_now] if toe_now else []), *wet_now], [], list(plan.watercourses) + drawn_water)
            arm = routed if len(routed) >= 2 else clip_to_clear(arm, fabric, WEB_FABRIC_GAP)
        arm = s.trim_off_marsh(arm)
        if len(arm) >= 2:
            if _arm_crossing_accidental(arm, raw_arms[ai], kept):
                continue  # pragma: no cover - no rolled map currently trips the drop; the decision logic is unit-tested via _arm_crossing_accidental
            kept.append((arm, raw_arms[ai]))
            s.lane(arm, width=5, clearance=LANE_CLEARANCE, worn=True)
    s.M["meta"]["lane_skeleton"] = plan.lane_skeleton
    return kept


def stage_web(s: Settlement, plan: SitePlan) -> None:
    """STAGE 5b: the LANE WEB - the lanes that make every farmhouse reachable.

    WHY IT EXISTS. The record is decisive that a house in a nucleated cluster is reached by a way:
    "every house in the nucleated village is accessible via the interconnected system of narrow lanes
    and alleys" (research/homesteads.md). The skeleton alone does not deliver that - it is sized on
    the seat band while the houses spread wider - and before this stage a third of the pool's
    farmhouses stood more than 100 ft from any way, with a whole block of Sawada touched by nothing.

    WHY IT RUNS AFTER THE HOUSES, which is the opposite of every other lane on the map. `stage_ways`
    lays its lanes first precisely so the homesteads FRONT them, and the first attempt at this
    feature followed that rule and laid the web first too. It does not work, and the reason is worth
    keeping: a lane laid before the houses has to reserve its ground from a cluster that has not been
    packed yet, so it competes with the very houses it exists to serve. Given a normal corridor it
    pushed them outward and the four hamlets' long axes grew 51%, 58%, 15% and 97% - sprawl no check
    measures. Given a narrow one the houses collided with it instead. Laid AFTERWARDS the conflict
    simply is not there: placement is untouched, the cluster is exactly as compact as it was, and the
    web goes in the room that is actually left. That is also the truer account of these ways - an
    alley IS the residual gap between two plots, "colonized as semi private space by the adjoining
    house", not a corridor set aside in advance.

    THE FORM IS THE ROLLED KNOB, and the two differ by which axis is cut (`web_cuts` does both):
      - "alleys"    - laterals running back through the cluster, between columns of houses. The
                      accretive Chinese gridiron; it reads as a place that GREW.
      - "back_lane" - lanes running the length of the settlement, behind a rank. The planned form,
                      where the outermost one doubles as the village/farmland edge; it reads as a
                      place that was LAID OUT.
    Everything else about them is identical, which is what makes the knob honest: the difference a
    reader sees is the difference the research actually attests."""
    houses = [h for h in s.M.get("houses", []) if h.get("role") != "headman" or True]
    if len(houses) < 2 or not plan.envelope:
        return  # pragma: no cover - every hamlet seats several houses
    # A DISPERSED HAMLET HAS NO INTERNAL LANE NETWORK AT ALL, and that is the form, not a shortfall.
    # Tonami's farmsteads stand in the middle of their own holdings; what joins them to the world is
    # the connector out to the road, which `stage_track` has already drawn, and what joins them to
    # each other is the field baulks they walk on. Drawing a web here would erase the one thing that
    # makes the form legible at a glance. The two access checks are conditioned on the form to
    # match - see `research/homesteads.md`, "Does a hamlet have to be NUCLEATED at all?".
    if plan.settlement_form == "dispersed":
        s.M["meta"]["lane_skeleton"] = "none"
        return
    # THE FRAME SPANS THE HOUSES, MEASURED - not a multiple of the seat band. `CLUSTER_SPAN_FACTOR`
    # describes the row `front_row` offers seats along, and for a round or elongated cluster it is a
    # fair proxy for where the houses end up. For a CRESCENT it is not: the cluster wraps around the
    # field and its ends run well past the band, so the web's whole coordinate domain stopped short
    # of them and their houses could not be reached at all. That was every remaining cohort failure
    # and nothing else - all four were `shape=crescent`, worst house 431 ft from any way. The houses
    # are already placed by the time this runs, so there is no need to predict where they went.
    _ax, _ay = plan.seat["along"]
    _anchor = plan.seat["anchor"]
    _reach_along = max(abs((float(h["x"]) - _anchor[0]) * _ax + (float(h["y"]) - _anchor[1]) * _ay) for h in houses)
    frame = _margin_frame(plan, max(plan.seat["lat"] * CLUSTER_SPAN_FACTOR, _reach_along + BUNDLE_PITCH), near=[(float(h["x"]), float(h["y"])) for h in houses])
    proj = [frame.project((float(h["x"]), float(h["y"]))) for h in houses]
    arcs = [a for a, _ in proj]
    stands = [d for _, d in proj]
    # THE SKELETON GOES IN FIRST, in this same house-fitted frame (feature 126). It used to be laid
    # two stages earlier, before any house existed; now it is derived from where they actually went.
    # It runs before the web cuts so the web sees it as existing network to thread around and join,
    # which is what `_net_segs` reads.
    _lay_skeleton(s, plan, frame, arcs, stands)

    pad = 30.0  # a lane runs a little past the last steading it serves, not up to its wall

    # A WEB LANE SPANS THE HOUSES IT SERVES, AND NO MORE. Spanning the whole cluster's extent
    # instead leaves a tail running past the last steading into open ground at whichever end has no
    # houses at that cut - a tread that serves nobody, which is exactly what `lanes_reach_something`
    # exists to catch, and it was 13 of 24 cohort seeds. So each lane's extent is read off the
    # houses within reach of ITS OWN cut, not off the cluster as a whole.
    local = WEB_REACH_FT * 1.5

    def _extent(cuts_at: float, along: list[float], across: list[float]) -> tuple[float, float]:
        near_by = [v for v, w in zip(along, across, strict=False) if abs(w - cuts_at) <= local] or along
        return (min(near_by) - pad, max(near_by) + pad)

    lines: list[Poly] = []
    if plan.lane_web == "alleys":
        # A lateral spans the cluster's DEPTH at a cut along the margin. Straight in outline
        # coordinates, which is a gentle curve on the ground - it runs square out from the field
        # edge, which is the way a path between two plots actually leaves the paddy.
        for cut in web_cuts(arcs, WEB_REACH_FT, MIN_WEB_GAP):
            d0, d1 = _extent(cut, stands, arcs)
            lines.append([frame(cut, d0 + (d1 - d0) * i / 12.0) for i in range(13)])
    else:
        # A back lane spans the cluster's LENGTH at a cut in the standoff, sampled finely enough to
        # follow the margin's curve - a straight one parallels a curved field edge for a hundred feet
        # and then walks into the rice.
        cuts = web_cuts(stands, WEB_REACH_FT, MIN_WEB_GAP)
        for cut in cuts:
            a0, a1 = _extent(cut, arcs, stands)
            n = max(4, int((a1 - a0) / 40.0))
            lines.append([frame(a0 + (a1 - a0) * i / n, cut) for i in range(n + 1)])
        # ...AND THE CROSS-LINKS THAT MAKE IT A FRAMEWORK RATHER THAN A LADDER OF SEPARATE RUNGS.
        #
        # PARALLEL LANES NEVER MEET. That is arithmetic, not a bug to tune around, and it is why the
        # back-lane form came out of three settlement-reviews as two and three disconnected
        # components while the alleys form did not: an alley crosses the spine it branches from, a
        # back lane runs beside its neighbor forever. The source is not silent about this - the
        # planned form is "back lanes on each side of the main street WHICH, TOGETHER WITH THE MAIN
        # STREET ITSELF, PROVIDES A RECTANGULAR FRAMEWORK for the development of the village". A
        # framework is the parallels PLUS the ties. We were drawing only the parallels.
        #
        # The ties go where a lateral can physically pass - the gaps between steadings - which is the
        # same question `web_cuts` answers, asked along the other axis. They are spaced about three
        # bundle pitches apart rather than one, so the form still reads as a laid-out place with a
        # few cross-ways, not as the alleys form with extra steps.
        if cuts:
            lo_c, hi_c = min(cuts) - pad, max(cuts) + pad
            for tie in web_cuts(arcs, 3.0 * BUNDLE_PITCH, MIN_WEB_GAP):
                lines.append([frame(tie, lo_c + (hi_c - lo_c) * i / 8.0) for i in range(9)])

    crops = crop_polys(s)
    toe = s.toe_band() or None
    wet = [[(float(a), float(b)) for a, b in m["poly"]] for m in s.M.get("marshes", []) if m.get("role") != "defense" and m.get("poly")]
    hard = [list(plan.envelope), *crops, *([toe] if toe else []), *wet]
    fabric = _homestead_polys(s)
    walls = [poly for poly, _, _ in fabric]
    # The shelter belts, separately: a web lane may CROSS one but may not run its length.
    belts = [[(float(a), float(b)) for a, b in g["poly"]] for g in s.M.get("village_groves", []) if g.get("poly")]
    drawn_water = drawn_water_segs(s)  # channels AND streams - see the helper for why the streams were missing
    cands: list[Poly] = []
    for line in lines:
        # FINER SAMPLING AND A WIDER FABRIC MARGIN THAN THE DEFAULTS. A web lane runs among the
        # steadings rather than past them, so it gets many more chances to clip a corner: sampled
        # every 8 ft with a 6 ft margin it cut across dooryard gardens on 7 of 24 cohort seeds, both
        # endpoints of the offending step legally clear while the step between them crossed the bed.
        # 4 ft samples and an 8 ft margin close that; the cost is sampling time on a short line.
        cands.extend(clear_runs(line, hard, WEB_HARD_GAP, step=4.0, lines=list(plan.watercourses) + drawn_water, tight=walls, tight_margin=WEB_FABRIC_GAP))
    # DECIDE CONNECTIVITY BEFORE ANY INK GOES DOWN. A run that cannot be reached from the skeleton is
    # not drawn at all, which is only possible because the decision is made over CANDIDATES - once a
    # lane is drawn there is no clean way to take it back, and the version that judged each run as it
    # went could only ever refuse the ones it had not reached yet. Growing the component from the
    # skeleton outward also lets a run join THROUGH another web run, which is what a framework is.
    for run in _reachable_runs(cands, _net_segs(s)):
        _lay_web_lane(s, run, hard, walls, list(plan.watercourses) + drawn_water, belts=belts, houses=[(float(h["x"]), float(h["y"])) for h in houses])
    # A WEB LANE STOPS WHERE IT STOPS SERVING. Clipping ends an arm wherever the crop or a steading
    # happens to begin, which can leave a tail running on into bare grass - `lanes_reach_something`
    # is right to call that a tread that serves nobody. The engine already owns this trim; the web
    # simply has to ask for it after adding to the network.
    s.trim_lane_stubs()
    # STRAGGLERS COME AFTER THE TRIM, NEVER BEFORE IT. `trim_lane_stubs` drops any lane under its
    # 71 ft minimum, and a footpath from a door to the nearest way is about 65 ft by construction -
    # so run the other way round, every spur this pass drew was silently deleted again and the eight
    # unreached houses stayed exactly eight. A door path is short on purpose; it is not a stub.
    # ONE NETWORK FIRST, then the houses that it still does not reach. Order matters: a footpath
    # that joins an orphaned component is worth nothing while the component itself is an island.
    _join_orphan_ways(s, hard, walls, list(plan.watercourses) + drawn_water)
    # ...and close any break where one way was drawn as two. Before the stragglers: a house beside
    # the hole is served by the bridged street, and drawing it a footpath of its own first would be
    # curing the symptom.
    _bridge_collinear_breaks(s, hard, walls, list(plan.watercourses) + drawn_water)
    _serve_stragglers(s, plan, hard, fabric, list(plan.watercourses) + drawn_water)
    # ...AND JOIN ORPHANS AGAIN, LAST. The first pass runs before the bridges and the footpaths, so
    # it can only see the lanes that exist then - on cohort seed 39 that was FOUR of the twelve the
    # map finishes with, and the eight added afterwards formed a second network of their own. Every
    # house on that map is within 86 ft of a lane and twelve of them still counted as unreached,
    # because the lane serving them was not on the network the connector is on. A repair pass that
    # runs before the things it repairs is not a repair pass.
    # ...and CLOSE BREAKS again before joining, for the same reason the join runs twice: the
    # footpath pass draws lanes, and a lane drawn after the bridge pass can leave a hole the bridge
    # pass never saw. On cohort seed 48 the bridge found ZERO candidates and the finished map still
    # had a 78 ft hole in a street, because the hole did not exist yet when it looked.
    _bridge_collinear_breaks(s, hard, walls, list(plan.watercourses) + drawn_water)
    _join_orphan_ways(s, hard, walls, list(plan.watercourses) + drawn_water)
    # ...AND SWEEP THE DEBRIS, LAST OF ALL. `_WEB_MIN_FT` is applied when a run is proposed, but the
    # end-trim runs AFTER that and pulls a run back to its last serving point - so a lane that was
    # 60 ft when it passed the floor can be 4 ft by the time it is drawn. Mizuguchi shipped a 4.2 ft
    # tread with rounded caps standing 3.3 ft off a farmhouse wall, and Kashikawa 17, 25 and 29 ft
    # marks; at 1 px = 1 ft those read as dropped sticks, which is exactly what the floor's own
    # comment says it exists to prevent ("a 4 ft mark fronts nobody and reads as a speck of clipping
    # debris"). A floor that is only checked before the thing that shortens the run is not a floor.
    #
    # The connector and the field spur are exempt: they are not web lanes and their length is
    # whatever the journey needs.
    _debris = [i for i, ln in enumerate(s.M.get("lanes", [])) if not ln.get("connector") and len(ln.get("pts") or []) >= 2 and polyline_len([(float(x), float(y)) for x, y in ln["pts"]]) < _WEB_MIN_FT]
    for i in reversed(_debris):
        s.M["lanes"].pop(i)
    s.M["meta"]["lane_web"] = plan.lane_web


# How near a footpath's far end must come to an existing way to count as joining it. This is
# `lanes_reach_something`'s own way-reach, deliberately: a path that gets this close IS connected as
# far as the gate is concerned, and demanding better only threw away paths that served their house.
_LANE_JOIN_FT = 30.0  # inside lanes_reach_something's own 40 ft, with room to spare for a rounded end

# HOW FAR A FOOTPATH MAY WANDER, as a multiple of its own straight-line chord. A review measured
# every honest way on these maps at 1.00-1.34 and one accepted switchback at 3.54 - 271 ft of path
# to join two points 77 ft apart, folded back through the windbreak. 2.0 admits a path that goes
# properly round one steading, which is what the router draws, and still refuses a fold.
_PATH_DIRECTNESS = 2.0

# A LINK that joins two halves of one settlement may wander further than a door path. Going round a
# paddy is legitimately indirect, and the thing being bought is the difference between a dozen houses
# reachable and a dozen houses not.
_LINK_DIRECTNESS = 4.0

# A GAP THIS SHORT BETWEEN TWO NEAR-COLLINEAR ENDS IS ONE WAY DRAWN AS TWO. 150 ft is about a
# household and a half of frontage - far enough that a real interruption (a wellhead, a bed, a
# clump) has somewhere to sit, close enough that the eye reads the two pieces as one street with a
# hole in it. The bearing bound is tighter than the fan rule's: these ends have to point AT each
# other, not merely lie alongside.
# THE SHORTEST THING THAT IS STILL A WAY. `_LANE_MIN_FT` (71) is the floor for a lane the
# homesteads FRONT and is right for one; a door path is legitimately about 65 ft and would be deleted
# by it. But there is a floor below which nothing is a way at all: Sawada shipped 4 ft, 12 ft and
# 20 ft fragments, left behind when the end-trim pulled a path back to its last serving point. A
# 4 ft mark fronts nobody and reads as a speck of clipping debris. 30 ft is under half a door path.
_WEB_MIN_FT = 30.0

_TREAD_TOUCH_FT = 6.0
"""The gap below which two treads are already ONE piece of ink and there is nothing to bridge.

A lane's drawn tread is a few feet wide, so anything under about this reads as a join on the sheet.
It is deliberately NOT `_LANE_JOIN_FT`: that is the gate's REACH tolerance ("is this house served"),
and using a reach figure as an ink-continuity figure is what let 21-29 ft holes ship as connected."""

_BREAK_SPAN_FT = 150.0
_BREAK_BEARING_DEG = 15.0


def _reach(c: Pt, path: Poly) -> float:
    """How near a polyline comes to a point - the same measurement `farmhouses_reach_a_way` makes."""
    return min(math.dist(c, seg_closest(c[0], c[1], a, b)) for a, b in zip(path, path[1:], strict=False))


def _reachable_runs(cands: Sequence[Poly], seed_segs: Sequence[tuple[Pt, Pt]]) -> list[Poly]:
    """The candidate runs that can be REACHED from the existing way network, growing outward.

    A run joins if it comes within `_LANE_JOIN_FT` of the skeleton or of a run already admitted, so a
    back lane may join through a cross-tie and a tie may join through a back lane - which is exactly
    what makes a framework a framework. Everything left over is an island and is never drawn.

    Deciding this over candidates rather than over drawn lanes is the whole point: a lane that has
    been inked cannot be taken back, so an earlier version - which asked each run as it was about to
    be drawn whether it touched anything yet - refused runs merely for being early in the loop and
    admitted islands that happened to be laid first. Order should not decide what a village looks
    like.

    ADJACENCY IS COMPUTED ONCE, over a bounding-box prefilter, and the runs are subsampled to a
    stride before any distance is measured. The naive version re-measured every admitted segment
    against every remaining run on every pass - a candidate is ~175 points at the 4 ft clip step and
    the admitted network grows without bound, so it went quadratic in samples on top of quadratic in
    passes and killed a cohort worker outright. The prefilter is the index and the stride is the
    resolution; neither decides anything, which is the project's standing rule for both."""
    runs = [r for r in cands if len(r) >= 2]
    if not runs:
        return []
    stride = max(1, int(_LANE_JOIN_FT / 8.0))
    thin = [r[::stride] + [r[-1]] for r in runs]

    def box(pts: Sequence[Pt]) -> tuple[float, float, float, float]:
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        return (min(xs) - _LANE_JOIN_FT, min(ys) - _LANE_JOIN_FT, max(xs) + _LANE_JOIN_FT, max(ys) + _LANE_JOIN_FT)

    boxes = [box(r) for r in thin]

    def near(i: int, j: int) -> bool:
        a, b = boxes[i], boxes[j]
        if a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]:
            return False
        return any(seg_dist(q[0], q[1], u, v) <= _LANE_JOIN_FT for q in thin[i] for u, v in zip(thin[j], thin[j][1:], strict=False))

    seed_pts = [q for a, b in seed_segs for q in (a, b)]
    seed_box = box(seed_pts) if seed_pts else None
    reached = set()
    for i, r in enumerate(thin):
        if seed_box is None:
            continue
        bx = boxes[i]
        if bx[2] < seed_box[0] or seed_box[2] < bx[0] or bx[3] < seed_box[1] or seed_box[3] < bx[1]:
            continue
        if any(seg_dist(q[0], q[1], u, v) <= _LANE_JOIN_FT for q in r for u, v in seed_segs):
            reached.add(i)
    if seed_box is None:  # pragma: no cover - a hamlet always has a skeleton by now
        reached = {0}
    frontier = list(reached)
    while frontier:
        i = frontier.pop()
        for j in range(len(thin)):
            if j not in reached and near(i, j):
                reached.add(j)
                frontier.append(j)
    return [runs[i] for i in sorted(reached)]


def _route(start: Pt, goal: Pt, hard: list[Poly], walls: Sequence[Poly], water: list[tuple[Pt, Pt]], cell: float = 10.0, gap: float = WEB_FABRIC_GAP, pad_mult: float = 0.75) -> Poly:
    """A walkable route from a door to a way, THREADING the steadings rather than assuming a line.

    A straight run plus a few dog-legs was the first two attempts and it is not enough. Measured on
    the in-gate cohort once everything else was fixed, EVERY remaining unreachable farmhouse was
    `hard-clear` and `fabric-blocked` - the paddy, the marsh and the toe were all out of the way, and
    the only thing between the house and the lane was other people's yards and gardens. That is a
    routing problem, and routing problems want a router: a fixed set of offsets either overshoots on
    a short run (a switchback, which a review caught) or misses the gap on a long one.

    Dijkstra on a coarse lattice, then string-pulled. The lattice is the INDEX - it decides nothing,
    because every shortcut is re-tested against the real geometry by `_clear_link` before it is
    taken, so the drawn path is exactly as legal as one drawn by hand. 12 ft cells because the gaps
    these paths thread are `MIN_WEB_GAP` (16 ft) at their narrowest, and a lattice coarser than the
    gap cannot see the gap.

    Returns [] when there is genuinely no way through - which is a real answer, and better than the
    caret a review found on Mizuguchi: a 38 ft mark drawn 71 ft from the house it served, touching
    nothing, to cure a one-foot violation."""
    span = math.dist(start, goal)
    if span < 1.0:  # pragma: no cover - the caller never routes to where it already is
        return [start, goal]
    # THE SEARCH BOX HAS TO BE BIG ENOUGH FOR THE DETOUR, not just for the gap. A path between two
    # steadings needs a little room either side; a link that has to get AROUND a paddy needs as much
    # room as the paddy is wide, and at 0.75 the box simply did not contain the way round - the
    # router reported NO ROUTE for a journey that plainly exists. `pad_mult` is how far the caller
    # thinks the detour might reach.
    pad = max(80.0, span * pad_mult)
    x0, x1 = min(start[0], goal[0]) - pad, max(start[0], goal[0]) + pad
    y0, y1 = min(start[1], goal[1]) - pad, max(start[1], goal[1]) + pad
    nx, ny = int((x1 - x0) / cell) + 1, int((y1 - y0) / cell) + 1
    if nx * ny > 90000:  # pragma: no cover - the pad is bounded, so the grid is too
        return []

    def to_pt(ix: int, iy: int) -> Pt:
        return (x0 + ix * cell, y0 + iy * cell)

    # THE LATTICE TESTS CELL CENTERS, SO IT MUST CLEAR HALF A CELL MORE THAN THE PATH NEEDS.
    #
    # A cell whose CENTER is `gap` from a wall is marked free, and the drawn line through that cell
    # can pass half a cell nearer than its center does - at a 14 ft cell, seven feet nearer. Measured:
    # three web lanes on cohort seed 11 came within 4.0 ft of a farmhouse corner having been planned
    # at 7, and a farmhouse ended up standing on the lane. Inflating the planning clearance by half
    # the cell's diagonal makes "this cell is free" mean "every point in this cell is clear", which is
    # what the rest of the router assumes it means.
    _plan_gap = gap + cell * 0.71
    free = [[bool(clear_runs([to_pt(ix, iy), to_pt(ix, iy)], hard, WEB_HARD_GAP, step=cell, lines=water, tight=walls, tight_margin=_plan_gap, floor=0.0)) for ix in range(nx)] for iy in range(ny)]
    sx, sy = min(nx - 1, max(0, round((start[0] - x0) / cell))), min(ny - 1, max(0, round((start[1] - y0) / cell)))
    gx, gy = min(nx - 1, max(0, round((goal[0] - x0) / cell))), min(ny - 1, max(0, round((goal[1] - y0) / cell)))
    free[sy][sx] = free[gy][gx] = True  # the two given endpoints are the caller's, not the lattice's to refuse
    dist = {(sx, sy): 0.0}
    prev: dict[tuple[int, int], tuple[int, int]] = {}
    heap = [(0.0, sx, sy)]
    while heap:
        d, ix, iy = heapq.heappop(heap)
        if (ix, iy) == (gx, gy):
            break
        if d > dist.get((ix, iy), 1e18):
            continue
        for dx2 in (-1, 0, 1):
            for dy2 in (-1, 0, 1):
                jx, jy = ix + dx2, iy + dy2
                # A DIAGONAL MAY NOT CUT A BLOCKED CORNER. Cell centers can both be clear while the
                # step between them clips the corner of a steading standing between them - so the
                # planned route was not actually walkable and failed its own acceptance test a moment
                # later, having been "found". Requiring both orthogonal neighbors makes the lattice
                # tell the truth about what it can walk.
                if (dx2 or dy2) and 0 <= jx < nx and 0 <= jy < ny and free[jy][jx] and (not (dx2 and dy2) or (free[iy][jx] and free[jy][ix])):
                    nd = d + math.hypot(dx2, dy2) * cell
                    if nd < dist.get((jx, jy), 1e18):
                        dist[(jx, jy)] = nd
                        prev[(jx, jy)] = (ix, iy)
                        heapq.heappush(heap, (nd, jx, jy))
    if (gx, gy) not in dist:
        return []
    path: Poly = []
    cur = (gx, gy)
    while cur != (sx, sy):
        path.append(to_pt(*cur))
        cur = prev[cur]
    path.append(start)
    path.reverse()
    path[-1] = goal
    # STRING-PULL against the real geometry, so the lattice never shows in the drawing.
    out: Poly = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        # STRING-PULL AT THE CLEARANCE THE LATTICE PLANNED WITH, not at the default. Validating
        # shortcuts more strictly than the route was planned produced paths that failed their own
        # acceptance test a moment later - the router found a way through at 5 ft and the pull then
        # refused every shortcut along it at 7, leaving a chain of lattice steps whose diagonals
        # clipped the corners the cell centers had cleared. One number, used by both.
        while j > i + 1 and not _clear_link(path[i], path[j], hard, walls, water, gap=gap):
            j -= 1
        out.append(path[j])
        i = j
    return out


def _clear_link(a: Pt, b: Pt, hard: list[Poly], walls: Sequence[Poly], water: list[tuple[Pt, Pt]], gap: float = WEB_FABRIC_GAP) -> bool:
    """Is the short run between two points walkable? Used before extending a lane end onto the way
    it meets, so a junction is drawn as a touch without the touch crossing anything."""
    span = math.dist(a, b)
    if span < 1.0:
        return True
    # THE WHOLE LINK, NOT A PIECE OF IT. Accepting the first surviving run let a snap be drawn across
    # ground that had been clipped out of the middle - the run existed, it just was not the gap being
    # bridged - and the lane ink then crossed a house or a garden bed
    # (`features_do_not_overlap`, `houses_clear_of_lanes`). A link is walkable only if it survives
    # end to end.
    runs = clear_runs([a, b], hard, WEB_HARD_GAP, step=3.0, lines=water, tight=walls, tight_margin=gap, floor=0.5)
    return any(polyline_len(r) >= span - 3.0 for r in runs)


def _aim_off(prev: Pt, tip: Pt, target: Pt) -> float:
    """How far off this end's outward heading is from aiming at `target`, in degrees.

    The honest test of "these two ends are one way with a hole in it": each end has to be heading
    INTO the gap toward the other, which is a statement about each end separately and about the line
    between them - not a comparison of the two headings with each other."""
    out = math.degrees(math.atan2(tip[1] - prev[1], tip[0] - prev[0]))
    aim = math.degrees(math.atan2(target[1] - tip[1], target[0] - tip[0]))
    return abs((out - aim + 180.0) % 360.0 - 180.0)


def _bridge_collinear_breaks(s: Settlement, hard: list[Poly], walls: Sequence[Poly], water: list[tuple[Pt, Pt]]) -> int:
    """Close a gap where ONE way has been drawn as two, and the ground between them is walkable.

    A lane that stops and resumes 110 ft further on, 8 degrees off collinear, is not two arms - it is
    one street with a hole in the middle of the built-up frontage, and both its ends read as rounded
    caps dying in bare grass. `lanes_reach_something` passes them because it tests each END
    independently: an end 83 ft from a house CENTRE is "fronting" it even when that is 55 ft from the
    wall, i.e. out past the dooryard.

    THE TEST IS WHETHER THE GAP IS WALKABLE, which is what makes this a defect rather than an
    observation. Two near-collinear ends with a wellhead or a garden bed between them are honestly
    interrupted - the way goes round, or stops, because something is there. Two with nothing between
    them are one way that was drawn in two pieces, and the fix is to draw the piece that is missing.

    Found by a peer session's review of Sawada, where the ends sit either side of the cluster's own
    middle; the same shape survives on other maps and is a plain gap in the network."""
    made = 0
    # TWELVE PASSES, not four. Each closure adds a lane whose own ends sit beside existing ones, so a
    # map with several breaks needs several rounds - and Sawada ran out at four with three breaks
    # still open, which reads as the fix not working rather than as the loop giving up. The bound
    # exists only so a pathological map cannot spin; a hamlet uses two or three.
    for _ in range(12):
        ways = [[(float(x), float(y)) for x, y in ln["pts"]] for ln in s.M.get("lanes", [])]
        best = None
        for i, li in enumerate(s.M.get("lanes", [])):
            if li.get("connector") or len(ways[i]) < 2:
                continue
            for j, lj in enumerate(s.M.get("lanes", [])):
                if j <= i or lj.get("connector") or len(ways[j]) < 2:
                    continue
                for ta, pra in ((ways[i][0], ways[i][1]), (ways[i][-1], ways[i][-2])):
                    for tb, prb in ((ways[j][0], ways[j][1]), (ways[j][-1], ways[j][-2])):
                        gap = math.dist(ta, tb)
                        # SHORT GAPS ARE THE ONES THAT MATTER, and they used to be excluded outright.
                        #
                        # The lower bound was `_LANE_JOIN_FT` (30), on the reasoning that anything
                        # closer than the gate's join tolerance is already "connected". It is not
                        # connected in INK: at 1 px = 1 ft a 29 ft hole is 29 px of bare grass
                        # between two ~4 px treads, which reads as two dropped sticks, and the gate
                        # is silent precisely BECAUSE its own tolerance erases it. Feature 126 made
                        # this visible - deriving the lanes from the houses produces more short
                        # breaks - and three settlement-reviews found it independently on three
                        # maps: Inashiro went from one ink component at HEAD to four, with six
                        # houses 105-243 ft from the connected network behind holes of 28.4, 28.7
                        # and 29.4 ft.
                        #
                        # The floor is now the tread's own width: below that there is nothing to
                        # bridge, because the two treads already touch.
                        if not (_TREAD_TOUCH_FT < gap <= _BREAK_SPAN_FT):
                            continue
                        # ...and a SHORT gap does not have to be collinear. The bearing test exists
                        # to tell "one way with a hole in it" from "two arms that happen to end near
                        # each other", and over 150 ft that distinction is real. Over 25 ft it is
                        # not: a back lane following a curved field margin breaks at 37 deg of
                        # aim-off and is still one lane. So the test applies from `_LANE_JOIN_FT` up,
                        # and a shorter hole is closed on proximity alone.
                        if gap > _LANE_JOIN_FT and (_aim_off(pra, ta, tb) > _BREAK_BEARING_DEG or _aim_off(prb, tb, ta) > _BREAK_BEARING_DEG):
                            continue  # two arms, not one way
                        # POINTING AT EACH OTHER MEANS EACH END'S OUTWARD DIRECTION AIMS AT THE
                        # OTHER END - not that the two outward bearings are similar. Two ends facing
                        # across a gap have OPPOSITE outward bearings (one runs east, the other runs
                        # west into the same hole), so comparing them for similarity tests the wrong
                        # thing entirely: it selects pairs pointing the SAME way, which is two
                        # parallel arms, and misses the collinear break it was written for. Caught by
                        # a unit test built from the textbook case rather than from a map.

                        # ...unless a third way already spans it. Closing a break leaves the two
                        # original ends where they were, joined THROUGH the new lane - so without
                        # this the pass re-bridges the same pair every round and burns its budget on
                        # work already done.
                        if any(
                            k not in (i, j)
                            and len(o) >= 2
                            and min(seg_dist(ta[0], ta[1], a2, b2) for a2, b2 in zip(o, o[1:], strict=False)) <= _LANE_JOIN_FT
                            and min(seg_dist(tb[0], tb[1], a2, b2) for a2, b2 in zip(o, o[1:], strict=False)) <= _LANE_JOIN_FT
                            for k, o in enumerate(ways)
                        ):
                            continue
                        if best is None or gap < best[0]:
                            best = (gap, ta, tb, float(li.get("w", 5)), float(lj.get("w", 5)))
        if best is None:
            return made
        # PLAN AT THE CLEARANCE IT WILL BE DRAWN AT. A bridge inherits the width of the street it
        # completes - 5 or 6 ft - so planning it at the FOOTPATH clearance leaves about a foot
        # between a 3 ft half-tread and a wall, and `houses_clear_of_lanes` says so. A footpath is
        # the one way on the map walked in single file; a street closing its own gap is not.
        span = _route(best[1], best[2], hard, walls, water, gap=WEB_FABRIC_GAP)
        if not span or polyline_len(span) > _PATH_DIRECTNESS * max(best[0], 1.0):
            return made  # something is genuinely in the way; the interruption is honest
        if not _draw_web(s, span, int(max(best[3], best[4]))):
            return made  # pragma: no cover - a bridge is always longer than the debris floor
        made += 1
    return made  # pragma: no cover - twelve bridges is far more than any hamlet needs


def _join_orphan_ways(s: Settlement, hard: list[Poly], walls: Sequence[Poly], water: list[tuple[Pt, Pt]]) -> int:
    """Link any way that is not part of the settlement's one network - INCLUDING the skeleton's own.

    Found by the transitive `farmhouses_reach_a_way`, and it turned out not to be the web's fault at
    all: on a cohort hamlet the skeleton's two arms were clipped apart from the arm the connector
    leaves by, so they formed an island of their own, and every house they served counted as
    unreached. That is a pre-existing defect - it predates this feature and nothing could see it
    while the check measured distance to any polyline - and it is fixed here rather than ledgered,
    per Principle XIV.

    The link is a routed path, so it threads the steadings like any other; if no route exists the
    component stays orphaned and the gate says so, which is the honest outcome."""
    made = 0
    for _ in range(6):
        ways = [[(float(x), float(y)) for x, y in ln["pts"]] for ln in s.M.get("lanes", [])]
        if len(ways) < 2:
            return made
        seed = next((i for i, ln in enumerate(s.M["lanes"]) if ln.get("connector")), 0)
        main = {seed}
        grew = True
        while grew:
            grew = False
            for i, w in enumerate(ways):
                if i in main or len(w) < 2:
                    continue
                # MEMBERSHIP IS DECIDED BY TOUCH, NOT BY REACH - and getting that wrong is why this
                # pass could not see the very gaps it exists to close. `_LANE_JOIN_FT` (30) is the
                # gate's REACH tolerance: "is this house served by that way". Used here it says a
                # tread lying 25 ft from the network is already part of it, so the fragment is never
                # classified an orphan and no link is ever routed - while the sheet shows 25 px of
                # bare grass between two 4 px treads.
                #
                # Measured on Inashiro (feature 126, three settlement-reviews found it
                # independently): one ink component at HEAD became four, with six houses 105-243 ft
                # from the CONNECTED network behind holes of 28.4, 28.7 and 29.4 ft - every one of
                # them under 30 and therefore invisible to this loop.
                if any(_net_reach(w, list(zip(ways[j], ways[j][1:], strict=False))) <= _TREAD_TOUCH_FT for j in main if len(ways[j]) >= 2):
                    main.add(i)
                    grew = True
        orphans = [i for i in range(len(ways)) if i not in main and len(ways[i]) >= 2]
        if not orphans:
            return made
        main_segs = [seg for j in main for seg in zip(ways[j], ways[j][1:], strict=False)]
        # EVERY CANDIDATE, NEAREST FIRST - not just the nearest one. Giving up on the first orphan
        # that cannot be routed abandoned the whole pass, and with it every OTHER orphan that could
        # have been linked. Measured: seed 39 came out with 12 lanes of which only 5 were in the
        # connector's component, and all 12 of its houses counted as unreached - while being within
        # 86 ft of a lane, just not one on the network. Seed 9 the same, 11 of 11. That is the entire
        # reach residue on those maps: not a house without a way, a way without the network.
        cands = sorted(
            ((math.dist(v, q), v, q) for i in orphans for v in ways[i] for q in [min((seg_closest(v[0], v[1], a, b) for a, b in main_segs), key=lambda z: math.dist(v, z))]),
            key=lambda c: c[0],
        )
        link, best = None, None
        for cand in cands[:40]:
            # A LINK MAY GO THE LONG WAY ROUND, AND MAY BE PLANKED. Joining the network is worth a
            # detour that a footpath to a door would not be: these two halves of one hamlet are
            # otherwise separated by its own field, and the alternative to an indirect link is a
            # dozen houses that count as unreachable. Water is crossable for the same reason it is
            # for a footpath - `stage_crossings` decks it afterwards.
            # PLAN AT THE CLEARANCE IT WILL BE DRAWN AT - the third and last place this was wrong.
            # A link inherits the width of the way it joins, so planning it at the FOOTPATH clearance
            # leaves about a foot between a 3 ft half-tread and a wall, and a farmhouse ends up
            # standing on the lane (cohort seed 11). Only the true single-file footpath gets the
            # footpath clearance; a street, a bridge and a link are all drawn wider than one.
            _try = _route(cand[1], cand[2], hard, walls, [], gap=WEB_FABRIC_GAP, pad_mult=2.0, cell=14.0)
            # ...AND IF THE OPEN CLEARANCE FINDS NO ROUTE, TRY SQUEEZING PAST THE WALL.
            #
            # The two halves of a settlement are worth an alley that a fresh lane would not be. On
            # Inashiro two web lanes of 57 and 70 ft sat 28.4 and 28.7 ft from the network and could
            # not be linked at all, because a steading's corner falls inside `WEB_FABRIC_GAP` of
            # every joining line - so the map shipped three separate networks where HEAD had one.
            #
            # A tighter link is not a worse lane, it is the RIGHT lane: the sources describe exactly
            # this way as "colonized as semi-private space by the adjoining house", barely more than
            # the gap between two walls (research/homesteads.md). What must not happen is a tread
            # drawn ON a wall, and that is a separate guarantee - `_house_on_a_tread` and
            # `houses_clear_of_lanes` both measure the drawn footprint against the drawn tread, and
            # neither is relaxed here. This only lets the ROUTE plan closer.
            if not _try:
                _try = _route(cand[1], cand[2], hard, walls, [], gap=WEB_FABRIC_GAP * 0.45, pad_mult=1.0, cell=8.0)
            if _try and polyline_len(_try) <= _LINK_DIRECTNESS * max(cand[0], 1.0):
                link, best = _try, cand
                break
        if link is None or best is None:
            return made
        link = _trim_to_service(link, [sg for j in main for sg in zip(ways[j], ways[j][1:], strict=False)], [(float(q["x"]), float(q["y"])) for q in s.M.get("houses", [])])
        _w = max(
            (
                float(_l.get("w", 3))
                for _l in s.M.get("lanes", [])
                if len(_l.get("pts") or []) >= 2
                and _net_reach(link, list(zip([(float(x), float(y)) for x, y in _l["pts"]], [(float(x), float(y)) for x, y in _l["pts"]][1:], strict=False))) <= _LANE_JOIN_FT
            ),
            default=3.0,
        )
        _draw_web(s, link, int(_w))
        made += 1
    return made  # pragma: no cover - six links is far more than any hamlet needs


def _net_segs(s: Settlement) -> list[tuple[Pt, Pt]]:
    """Every drawn way on the map right now, as segments."""
    return [((float(p[0]), float(p[1])), (float(q[0]), float(q[1]))) for ln in s.M.get("lanes", []) for p, q in zip(ln["pts"], ln["pts"][1:], strict=False)]


def _draw_web(s: Settlement, pts: Poly, width: int = 3, houses: Sequence[Pt] = ()) -> bool:
    """Draw a web lane, unless it is debris. See `_WEB_MIN_FT`.

    SHORT IS NOT THE SAME AS USELESS, and conflating them cost more than the debris did. A blunt
    length floor refuses the door path of a steading that sits close to the network - which is
    exactly the house that most needs one - and the 48-seed sweep went from 6 unreached-house seeds
    to 17 the moment the floor went in. So a short run is refused only when it EARNS nothing: if it
    brings a house inside the reach that is outside it now, it is a way, whatever its length."""
    if len(pts) < 2:
        return False
    if polyline_len(pts) < _WEB_MIN_FT:
        segs = _net_segs(s)
        earns = any(_reach(h, pts) <= WEB_REACH_FT and (not segs or min(seg_dist(h[0], h[1], a, b) for a, b in segs) > WEB_REACH_FT) for h in houses)
        if not earns:
            return False
    s.lane(pts, width=width, clearance=WEB_CLEARANCE, worn=True)
    # Flagged so `lane_frontage` does not offer seats along it. A web lane is SERVICE - it threads
    # behind and between the steadings - and inviting new houses onto the way that exists to reach
    # the old ones is how the cluster starts sprawling again.
    s.M["lanes"][-1]["web"] = True
    return True


def _trim_to_service(run: Poly, segs: Sequence[tuple[Pt, Pt]], houses: Sequence[Pt]) -> Poly:
    """Pull a run's ends back to the last point that actually serves something.

    `lanes_reach_something` asks of every internal lane end that it reach another way within 40 ft or
    a farmhouse within 90; a web lane's ends come out of the clipper, which stops where the ground
    stops being walkable and has no opinion about whether anything is there. Trimming BEFORE the ink
    goes down is better than trimming after: `trim_lane_stubs` drops anything under its 71 ft floor,
    which is the right rule for a skeleton arm and would delete the door paths this feature exists to
    draw."""

    def serves(q: Pt) -> bool:
        return (any(seg_dist(q[0], q[1], a, b) <= 40.0 for a, b in segs) if segs else False) or any(math.dist(q, h) <= 90.0 for h in houses)

    out = list(run)
    while len(out) > 2 and not serves(out[-1]):
        out.pop()
    while len(out) > 2 and not serves(out[0]):
        out.pop(0)
    return out


def _lay_web_lane(s: Settlement, run: Poly, hard: list[Poly], walls: list[Poly], water: list[tuple[Pt, Pt]], belts: Sequence[Poly] = (), houses: Sequence[Pt] = ()) -> bool:
    """Draw one web lane - but ONLY if it joins the way network, and TOUCHING it where it joins.

    A WEB THAT DOES NOT JOIN UP IS NOT A WEB, and this is the rule that makes the name honest. Three
    settlement-reviews found the same defect independently on three different maps: the lanes reached
    the houses and reached nothing else. Sawada drew six web lanes of which four touched no other
    way, so seven of its nineteen houses were "served" by an island whose nearest real lane was still
    136-296 ft off - exactly where they had been before the feature. Inashiro came out as three
    separate components with a 110 ft gap between them. The research this feature cites is explicit
    that the thing being reproduced is "the INTERCONNECTED system of narrow lanes and alleys", so a
    lane that connects to nothing is not an alley, it is a yard path.

    Two distinct jobs, and both were missing:

      - JOIN. A run whose nearest end is already within `_LANE_JOIN_FT` counts as arriving; one that
        is further off gets a link drawn to the network, and if the link cannot be drawn the run is
        not drawn either. Refusing to draw is the right answer - the alternative is ink that looks
        like a way and is not one.
      - TOUCH. Acceptance and INK are different tolerances, and conflating them is what left Inashiro
        with a lane stopping 12.7 ft short of the junction it aimed at, a visible break of about 19
        px on the sheet. So the joining end is extended onto the way it meets. The gate reach can
        stay where it is; it is then satisfied by construction rather than by rounding.

    Also refuses a run that merely SHADOWS an existing way - Inashiro laid a back lane a median 10 ft
    from a skeleton lane for its whole length, which reads as one lane accidentally drawn twice.
    `MIN_WEB_GAP` keeps the web's own cuts apart; nothing was keeping a cut off the lanes already
    there."""
    segs = _net_segs(s)
    if len(run) < 2:  # pragma: no cover - clear_runs never returns a single point
        return False
    # TRIM FIRST, JOIN SECOND. The join is computed from the run's ENDS, so trimming afterwards moves
    # the end out from under the link that was drawn to it - which left a 187 ft lane whose start
    # stood 178 ft from any way, the exact dangling tread `lanes_reach_something` exists to catch.
    run = _trim_to_service(run, segs, houses)
    if len(run) < 2:  # pragma: no cover - a run always keeps two points
        return False
    if segs:
        # SHARING A CORRIDOR IS SHADOWING, whether the two lines are parallel or crossing. The test
        # was written against `MIN_WEB_GAP` (the room a lane needs to pass BETWEEN two steadings),
        # which is far too tight to describe two ways a reader sees as one: Inashiro laid a back lane
        # that crossed the connector mid-run and stayed within 30 ft of it for 91% of its length, and
        # the 18 ft test did not fire once. A reader reads them as one lane drawn twice, so the
        # threshold is what a reader can separate, not what a lane can squeeze through.
        # SHADOWING IS A LENGTH, NOT ONLY A FRACTION. A fraction alone lets a long run hide: a lane
        # that parallels the connector for 128 continuous feet at a median 16 ft measured 50%
        # shadowed against a 60% bar and was drawn. Doubled ink is doubled ink whether it is half the
        # run or four fifths of it, so the longest UNBROKEN shadowed stretch is capped at one bundle
        # pitch as well. Both clauses are needed - the fraction catches a short lane laid alongside
        # another for all of its length, the absolute catches a long one that eventually diverges.
        near_flags = [min(seg_dist(q[0], q[1], a, b) for a, b in segs) < WEB_SHADOW_FT for q in run]
        if sum(near_flags) > 0.6 * len(run):
            return False
        _step_ft = polyline_len(run) / max(len(run) - 1, 1)
        _worst = _cur = 0
        for _f in near_flags:
            _cur = _cur + 1 if _f else 0
            _worst = max(_worst, _cur)
        if _worst * _step_ft > BUNDLE_PITCH:
            return False
        # ...AND A LANE DOES NOT RUN THE LENGTH OF A SHELTER BELT. Crossing one costs the belt a
        # lane's width of wall, which is a fair price for a way that has somewhere to be; running
        # ALONG it splits one wind wall into two thinner ones and opens a slot down the middle. A
        # review measured a back lane 237 of 237 ft inside the belt, having deleted 15 of its 169
        # clumps, on a map whose notes already record this belt being damaged the same way once.
        for belt in belts:
            inside = sum(1 for q in run if point_in_poly(q[0], q[1], list(belt)))
            if inside * (polyline_len(run) / max(len(run), 1)) > 60.0:
                return False
        # THE WHOLE RUN ARRIVES, NOT JUST ITS TWO ENDS. Measuring only the endpoints is how the snap
        # came to draw a hairpin: a run whose BODY already passes 2.75 ft from a lane, but whose end
        # wandered 23.8 ft beyond it, got a perpendicular drawn back to the foot - a needle-thin
        # triangular loop hanging off the junction, which a review found on all four hamlets (turn
        # deviations of 158, 178, 110 and 107 degrees, against a pre-web maximum of 7). If the run
        # has already arrived somewhere along its length there is nothing to snap; the only thing
        # worth doing is trimming the short tail that carried on past.
        vert = [min(seg_dist(v[0], v[1], a, b) for a, b in segs) for v in run]
        k = min(range(len(vert)), key=lambda i: vert[i])
        if 0 < k < len(run) - 1 and vert[k] <= _LANE_JOIN_FT:
            head = polyline_len(run[: k + 1])
            tail = polyline_len(run[k:])
            if tail < 40.0:
                run = run[: k + 1]
            elif head < 40.0:
                run = run[k:]
            _draw_web(s, run, 3)
            return True
        d0, d1 = vert[0], vert[-1]
        end = 0 if d0 <= d1 else -1
        gap = min(d0, d1)
        p = run[end]
        q = min((seg_closest(p[0], p[1], a, b) for a, b in segs), key=lambda z: math.dist(p, z))
        if gap > _LANE_JOIN_FT:
            if math.dist(p, q) > WEB_REACH_FT * 2.0:
                return False
            link = [
                r for r in clear_runs([p, q], hard, WEB_HARD_GAP, step=4.0, lines=water, tight=walls, tight_margin=WEB_FABRIC_GAP, floor=12.0) if _reach(p, r) < 12.0 and _net_reach(r, segs) < 12.0
            ]
            if not link:
                return False
            # A HEALING LINK INHERITS THE WIDTH OF THE WAY IT JOINS. Laid at the web's own 3 ft
            # between two 5 ft lanes it renders as a neck with a round-cap knuckle at each step - a
            # review read it at 2x as a lollipop knob mid-street, and it is a repair scar rather than
            # a way. A link exists to make two lanes one; it should look like the lane it completes.
            _w = max(
                (
                    float(_l.get("w", 3))
                    for _l in s.M.get("lanes", [])
                    if _net_reach(link[0], list(zip([(float(x), float(y)) for x, y in _l["pts"]], [(float(x), float(y)) for x, y in _l["pts"]][1:], strict=False))) <= _LANE_JOIN_FT
                ),
                default=3.0,
            )
            _draw_web(s, link[0], int(_w))
        elif _clear_link(run[end], q, hard, walls, water):
            # SNAP ONLY IF THE GROUND BETWEEN IS CLEAR. Extending an end onto the way it meets is
            # what makes the junction read as a touch instead of a gap - but the few feet being
            # added are ground like any other, and adding them blind put lane ink across houses and
            # garden beds (`features_do_not_overlap`, `houses_clear_of_lanes` on every cohort seed
            # the moment snapping went in). If the gap is not walkable the lane simply ends where it
            # ended; a visible break is better than a lane through a wall.
            run = ([q, *run]) if end == 0 else ([*run, q])
    _draw_web(s, run, 3)
    return True


def _net_reach(path: Poly, segs: Sequence[tuple[Pt, Pt]]) -> float:
    """How near a candidate path comes to the EXISTING way network, at its nearest point."""
    return min(seg_dist(q[0], q[1], a, b) for q in path for a, b in segs)


def _serve_stragglers(s: Settlement, plan: SitePlan, hard: list[Poly], fabric: list[tuple[Poly, Pt | None, str]], water: list[tuple[Pt, Pt]]) -> None:
    """A FOOTPATH TO THE OUTLYING STEADING, for the few houses the web's regular cuts cannot reach.

    The web covers the cluster by construction, but its lanes are then clipped out of the crop, off
    the marsh and around the steadings - and a lane that loses its far end stops serving the houses
    that were out there. Rather than widen the whole web to survive its worst clip (which puts lanes
    everywhere to fix a problem in one place), each remaining house gets what a real farmstead on the
    edge of a hamlet has: a path of its own, running from the nearest way to its door.

    Drawn from the HOUSE outward, deliberately. Clipping truncates at the first blockage from the
    start, so starting at the door means the path keeps whatever length it can win from the house's
    side - and it is the house's end that has to be reached for the path to be worth anything."""
    # A HOUSE THAT EXHAUSTED EVERY TARGET WILL EXHAUST THE SAME ONES AGAIN (feature 126).
    #
    # This loop makes four passes, and each unserved house tries up to 60 targets. A house nothing
    # can reach therefore costs up to 240 routing calls, every one a failure, and it pays that bill
    # again on every pass. Measured on seed 25: three unreachable houses, `_route` called 817 times
    # for 278 s; the baseline's single unreachable house cost 388 calls and 103 s. The failures were
    # nearly the whole bill.
    #
    # This is the engine's SECOND documented performance shape - "the same scan run again over
    # ground that has not changed" (dev/performance.md) - and it takes the same cure as `SeatMemo`:
    # remember the refusal, and ASSERT the invariant rather than assume it. The memo keys on the
    # exact target list, so a house is skipped only when the candidate ways it would try are
    # identical to the ones it already failed against. Draw a lane anywhere near it and its targets
    # change, the key misses, and it is retried in full. That failure direction is the whole design:
    # a wrong memo costs the SPEEDUP, never a path.
    _exhausted: dict[int, tuple[tuple[float, float], ...]] = {}
    for _pass in range(4):
        lanes = [[(float(x), float(y)) for x, y in ln["pts"]] for ln in s.M.get("lanes", [])]
        segs = [(a, b) for ln in lanes for a, b in zip(ln, ln[1:], strict=False)]
        if not segs:
            return  # pragma: no cover - a hamlet always has its skeleton
        added = 0
        for h in list(s.M.get("houses", [])):
            c = (float(h["x"]), float(h["y"]))
            # THE LIVE NETWORK, NOT A SNAPSHOT. `segs` was read once per pass, so a house already
            # brought within reach by a path drawn two houses earlier IN THIS PASS still looked
            # stranded and got a second path of its own - Kashikawa's 29 ft lane 12, drawn for a
            # house that a previous lane had already taken from 100.7 ft to 38.9, and which the new
            # lane then left at 70.5. A way exists because feet use it.
            segs = _net_segs(s)
            # SERVE WITH MARGIN, NOT TO THE MILLIMETRE. Triggering at exactly the reach means a
            # house at 99.7 ft is not a straggler and gets nothing, while one at 100.3 has a whole
            # path drawn for four inches of violation - the same bug at both ends. A review caught
            # the first half twice on the same steading ("satisfying the rule by 0.3 ft ... a re-roll
            # will flip it"), and it had indeed flipped back. Ten feet of headroom fixes both.
            if min(math.dist(c, seg_closest(c[0], c[1], a, b)) for a, b in segs) <= WEB_REACH_FT * 0.9:
                continue
            # Everything EXCEPT this steading's own house, yard, garden and shed - the path has to
            # be able to leave its own dooryard, and `of` says which features those are.
            # NOTHING BUILT STEPS ASIDE - not even this steading's own house. Exempting it was how
            # the path got out of its own dooryard, and it was also a license for the router to drive
            # straight THROUGH the farmhouse: seeds 41 and 43 came back with `houses_clear_of_lanes`
            # and `houses_off_corridors`, which is a lane drawn over a wall. The door is pushed clear
            # of the house instead (see `step` below), which solves the same problem without letting
            # a path cross anything.
            #
            # GROUND COVER IS NOT FABRIC, though. A footpath may cross grazing scrub and may run
            # along a tree belt - those are what the ground IS, not things built on it, and a review
            # confirmed "the only polygons they cross are the grazing commons, which is what a lane
            # crosses". Counting them walled an outlying steading in behind its own commons.
            # TWO OBSTACLE SETS, because a steading's own yard is ground you WALK but not ground a
            # lane is DRAWN on. `others` is everything solid and is what the drawn tread is clipped
            # against. `passable` additionally lets the route PLAN through this steading's own yard
            # and garden - on a hemmed-in farmstead the bundle wraps the house completely, so with
            # its own yard solid there is no doorstep and the router reports no route at all, when
            # what does not exist is the doorstep. Planning through it and drawing only what survives
            # the clip gives the answer the sources describe: the lane ends AT the yard, and the yard
            # is private ground the household crosses on foot.
            _mine = [id(poly) for poly, owner, kind in fabric if owner is not None and math.dist(owner, c) <= 1.0 and kind in ("threshing_yards", "gardens")]
            others = [poly for poly, _owner, kind in fabric if kind not in ("commons", "village_groves")]
            passable = [poly for poly in others if id(poly) not in _mine]
            # The door stands clear of the steading's own wall by the same margin every other lane
            # keeps, so it is a legal starting point with the house left in the obstacle set.
            step = math.hypot(float(h["w"]), float(h["h"])) / 2 + 8.0 + FOOTPATH_FABRIC_GAP
            # EVERY WAY WITHIN REACH IS A CANDIDATE, not merely the closest one. A path aimed at the
            # nearest lane can run the length of a neighbor's threshing yard and be refused for its
            # whole run, while a way ten feet further off is reachable across open ground - measured,
            # that was every one of the eight houses this pass was failing to serve. Real footpaths
            # go where there is room, so the candidates are tried nearest-first and the first one
            # that has room wins.
            targets = sorted((seg_closest(c[0], c[1], a, b) for a, b in segs), key=lambda q: math.dist(c, q))
            _served = False
            _key = tuple((round(float(t[0]), 1), round(float(t[1]), 1)) for t in targets[:60])
            if _exhausted.get(id(h)) == _key:
                continue  # same house, same candidate ways, same obstacles - a replay of a pass that already failed
            for tgt in targets[:60]:
                # The radius is generous on purpose. A steading the web could not reach is by
                # definition one whose nearest way is already beyond the reach, so a search bounded
                # at twice the reach gave up on exactly the houses that needed it - two of seed 3's,
                # at 171 and 201 ft, were never attempted at all. A long path is a real thing on the
                # edge of a hamlet; a house with no path is not.
                # THE DIRECTNESS BOUND IS THE LIMIT, not a radius. Capping candidate targets at
                # 3.5x the reach meant a steading 399 ft from the network never had a single target
                # tried, though a clear route to one existed - the cap was a guess at "too far" and
                # the path's own shape is the honest test. Kept only as a backstop against searching
                # the whole map.
                if math.dist(c, tgt) > WEB_REACH_FT * 8.0:
                    break
                # THE DOOR IS WHERE THERE IS ROOM FOR ONE, not wherever the target happens to lie.
                # Placed blindly along the bearing to the way, it lands in the steading's own
                # threshing yard whenever the way is on the yard's side - and the route then fails at
                # its very first cell, which reads as "no route exists" when what does not exist is
                # that particular doorstep. Ring the house and take the clear standing-place nearest
                # the direction of travel.
                dx, dy = unit(tgt[0] - c[0], tgt[1] - c[1])
                # ...and OUTWARD until there is room, not only around at one radius. A hemmed-in
                # farmstead has its own threshing yard and garden wrapped right around it, so every
                # point on a ring at the house's own standoff lies inside its own bundle and there is
                # no legal doorstep at all - which the router reports as "no route", when what does
                # not exist is the doorstep. Exempting the steading's own open ground was tried and
                # rejected: it bought this house nothing and cost an overlap on another seed. Walking
                # out past the yard is what a person does, and it keeps every footprint solid.
                door = next(
                    (
                        q
                        for q in sorted(
                            ((c[0] + math.cos(math.tau * k / 16) * (step + out), c[1] + math.sin(math.tau * k / 16) * (step + out)) for out in (0.0, 12.0, 24.0, 40.0, 60.0, 85.0) for k in range(16)),
                            key=lambda q: (math.dist(q, c), -((q[0] - c[0]) * dx + (q[1] - c[1]) * dy)),
                        )
                        if _clear_link(q, q, hard, passable, water, gap=FOOTPATH_FABRIC_GAP)
                    ),
                    (c[0] + dx * step, c[1] + dy * step),
                )
                # A FOOTPATH BENDS. The straight run is tried first and is usually right, but a path
                # that meets a neighbor's garden bed head-on should go round it rather than be
                # abandoned - which is what a person does, and abandoning it was the single biggest
                # residue left in the cohort once the overlaps were fixed. The dog-legs are one
                # waypoint pushed off the straight line, nearest offsets first, so a straight path
                # always wins when it exists and the bend is only as much as it has to be.
                mid = ((door[0] + tgt[0]) / 2, (door[1] + tgt[1]) / 2)
                px, py = -dy, dx
                cands = [[door, tgt]]
                # ...and a ROUTED candidate, which is what actually gets there when the straight run
                # and the bends do not. Tried after them so a straight path still wins when one
                # exists - the router will happily return a slightly wandering line where a ruler
                # would do.
                # A FOOTPATH MAY CROSS A DITCH; IT GETS A PLANK. The routed candidate is allowed
                # over a watercourse because `stage_crossings` runs after this and decks any way that
                # crosses one - the field spur and the connector already rely on that. Measured: an
                # outlying farmstead on seed 2 had NO route to the network at any clearance, and the
                # thing between it and the cluster turned out not to be a yard or the crop but a
                # ditch. A steading across a ditch is reached by a plank, not by being unreachable.
                # A FINER LATTICE FOR THE FOOTPATH WAS TRIED AND REVERTED - do not pull this lever
                # again. The arithmetic is genuinely suggestive: the router inflates its planning
                # clearance to gap + cell * 0.71 so that a free cell means every point in it is
                # clear, which at the default 10 ft cell is 11.1 ft for a footpath - it demands a
                # 22 ft corridor to plan through, while the gaps between neighboring steadings are
                # MIN_WEB_GAP, 16 ft. At a 5 ft cell the planning clearance is 7.6 ft and a 16 ft gap
                # fits. It reads like the explanation of every unreachable steading, and it is not.
                #
                # Measured end to end (2026-08-18), coarse-only against a coarse-then-fine fallback,
                # on cohort seed 5: 159.9s -> 672.3s, a 4.2x build, and the unserved count did not
                # move (2 either way). Seed 25 improved 4 -> 2 across the same afternoon and it is
                # tempting to credit this - it is not the cause: with the fallback DISABLED, seed 25
                # measures 2 as well. That gain came from a peer session's merge, and attributing it
                # here would have written a false why into the file.
                #
                # So the lattice is not what strands these houses, and 4x the generation time buys
                # nothing. What does strand them is recorded with the reach residue.
                routed = _route(door, tgt, hard, passable, [], gap=FOOTPATH_FABRIC_GAP)
                if routed:
                    cands.append(routed)
                # THE BEND IS A FRACTION OF THE RUN, not a fixed number of feet. Offsets of 40, 80
                # and 130 ft are a gentle correction on a 300 ft path and a switchback on an 80 ft
                # one - Inashiro drew 271 ft of path to join two points 77 ft apart, and once the
                # anti-fold rule was added to catch that, the same fixed offsets simply failed every
                # short path instead and left the house unreached. Scaling by the chord keeps every
                # candidate inside the 1.6 directness the rule allows, so the two rules stop fighting.
                chord = math.dist(door, tgt)
                cands += [[door, (mid[0] + sgn * px * k * chord, mid[1] + sgn * py * k * chord), tgt] for k in (0.2, 0.35, 0.5) for sgn in (1.0, -1.0)]
                hit: list[Poly] = []
                for cand in cands:
                    runs = clear_runs(cand, hard, WEB_HARD_GAP, step=4.0, lines=[] if cand is routed else water, tight=others, tight_margin=FOOTPATH_FABRIC_GAP, floor=20.0)
                    # JOINING THE NETWORK, not arriving at the point that was aimed at. A candidate
                    # is clipped into runs, and the run that survives is often a middle fragment
                    # that serves the house perfectly well and touches a DIFFERENT lane than the one
                    # the path was aimed down. Measured on seed 8: 1,566 of 2,309 attempts found a
                    # run and every one of them was thrown away by testing against `tgt` alone.
                    # A PATH BENDS; IT DOES NOT SWITCHBACK, and it must actually arrive at both ends.
                    #
                    # Three things were wrong here and all three were found by review rather than by
                    # the gate, because the gate measures distance and these are shapes. (1) The
                    # dog-leg waypoints were tried in order and the first that CLEARED was taken,
                    # with nothing scoring the result - so Inashiro accepted a 130 ft offset intact
                    # and drew 271 ft of path to join two points 77 ft apart, folding back through
                    # the windbreak and costing the shelter belt six clumps. (2) The house end was
                    # only required within `WEB_REACH_FT`, i.e. 100 ft, so Mizuguchi drew a 38 ft
                    # mark 71 ft from the house it served, touching nothing, to cure a ONE-FOOT
                    # violation - a caret floating in a field. (3) Neither end had to touch, so
                    # Inashiro's read as a free chevron with 24 ft of grass at one end and 13 at the
                    # other.
                    #
                    # So: the path must reach the DOOR, not merely the house's neighborhood; it must
                    # reach the network; and its length may not exceed `_PATH_DIRECTNESS` times its own
                    # chord, which is the band every honest way on these maps already sits in (1.00-1.34).
                    hit = [r for r in runs if _reach(c, r) <= WEB_REACH_FT and _net_reach(r, segs) <= _LANE_JOIN_FT and polyline_len(r) <= _PATH_DIRECTNESS * max(math.dist(r[0], r[-1]), 1.0)]
                    if hit:
                        break
                # THE TEST IS WHETHER THE PATH SERVES THE HOUSE, not whether it starts exactly at
                # the door. A run that begins a little way out - because the first few feet are
                # taken by a neighbor's yard - still puts a way within reach of this steading, which
                # is the whole requirement. Insisting on the door threw away runs that did the job.
                # BOTH ENDS HAVE TO EARN THEIR KEEP. Serving the house is the point, but a path
                # whose far end stops short of the way it was aimed at is a tread ending in bare
                # grass, which `lanes_reach_something` rightly refuses - and it was the single
                # biggest residue in the cohort (13 of 24 seeds) when only the house end was tested.
                if hit:
                    # Both ends SNAPPED, for the same reason a web lane's joining end is: acceptance
                    # tolerances are not ink tolerances, and a path that stops 13 ft short of the
                    # lane it aims at is drawn as a gap whatever the gate thinks of it.
                    # A PATH STOPS AT ITS FIRST CONTACT WITH THE NETWORK - it does not then travel
                    # ALONG it. The router has no cost term for running down an existing tread, so
                    # once it entered a lane's corridor it was free to follow it: a review measured
                    # 32.6 ft of a door path drawn on top of a back lane at 0.0-1.2 ft separation,
                    # 27% of its length as duplicate ink, showing on the sheet as a seam and a width
                    # discontinuity. Truncating at first contact also takes that path's directness
                    # from 1.57 to 1.14. The snap below closes whatever gap is left.
                    path = list(hit[0])
                    for _i, _v in enumerate(path):
                        if _i and min(seg_dist(_v[0], _v[1], _a, _b) for _a, _b in segs) <= _LANE_JOIN_FT:
                            path = path[: _i + 1]
                            break
                    join = min((seg_closest(path[-1][0], path[-1][1], a, b) for a, b in segs), key=lambda z: math.dist(path[-1], z))
                    if _clear_link(path[-1], join, hard, others, water):
                        path = [*path, join]
                    # NO EXTRA STEP TOWARD THE DOOR. The path already begins at `door`, which is the
                    # house's own half-diagonal plus eight feet - i.e. just outside the wall. Pushing
                    # a further point in at 0.6 of that standoff put the start of the lane INSIDE the
                    # farmhouse, and `houses_clear_of_lanes` and the overlap matrix both said so. The
                    # steading's own footprint is exempt from this path's obstacle list so that it
                    # can leave the dooryard; that exemption is not a license to draw through the
                    # house.
                    # The path's own start can have been clipped away from the door, so it gets the
                    # same end-trim every web lane gets - a footpath that begins in bare grass is a
                    # dangling tread whatever drew it.
                    path = _trim_to_service(path, segs, [(float(q["x"]), float(q["y"])) for q in s.M.get("houses", [])])
                    _draw_web(s, path, 3, houses=[c])
                    added += 1
                    _served = True
                    break
            if not _served:
                _exhausted[id(h)] = _key
        if not added:
            return


def stage_ways(s: Settlement, plan: SitePlan) -> None:
    """The lanes, laid BEFORE the houses because a lane is a no-build corridor the homesteads front.

    Three kinds, and each is derived from something already on the map:
      - the cluster's internal SKELETON (`skeleton_layout`, rolled), laid in the seat frame so it
        runs along the margin whatever direction the margin faces;
      - a SPUR from the skeleton to the nearest point of the field, because the reason these houses
        are here is the field and there must be a way to walk to it;
      - the CONNECTOR, the trodden track that leaves for the wider world. It starts at the
        skeleton's own gateway (the downslope exit the layout defines) and runs to the map edge, its
        bearing swung away from the crop until it clears - a track goes around a paddy, not through
        it. `connector_lane_runs_off_edge` requires it to actually reach the frame; the reason it
        must is that a path stopping mid-landscape reads as a dead end."""
    drain = None
    for ditch in s.M.get("field_ditches", []):
        if ditch.get("role") == "drain" and len(ditch["poly"]) >= 2:
            drain = [(float(v[0]), float(v[1])) for v in ditch["poly"]]
            break
    # EVERY watercourse on the map, not just the field's own ditches. The ways are routed to meet
    # water squarely and to keep their decks off the crop, and that is only as good as the list they
    # are handed: the STREAMS - the feed brook coming down to the intake, the drain brook leaving
    # the frame - are drawn in the two stages before this one and were missing from it, so a track
    # could cross one at a slant and `bridges_span_their_water` would fail on a deck too short for
    # the water beneath it.
    # ...and the DRAWN lines, not only the recorded ones. `field_channel` fillets its polyline before
    # drawing it (`fillet_polyline`, so a mitred corner does not spike), and it is the drawn line a
    # bridge gets placed on - so routing against the recorded one can send a way across a ditch at a
    # slant the router never saw. Same rule as the connector's own bow: measure what is drawn.
    plan.watercourses = [
        ((float(a[0]), float(a[1])), (float(b[0]), float(b[1])))
        for rec in list(s.M.get("field_ditches", [])) + list(s.M.get("channels", [])) + list(s.M.get("streams", []))
        for a, b in zip(rec["poly"], rec["poly"][1:], strict=False)
    ] + [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for rec in s.M.get("drawn_channels", []) for a, b in zip(rec["pts"], rec["pts"][1:], strict=False)]
    seat = seat_cluster(plan, dry_plots=crop_polys(s), drain=drain, toe=s.toe_band() or None)
    plan.seat = seat
    # THE SITE'S BACK IS THE WINDWARD SIDE, and where the two disagree the site wins.
    #
    # The wind is derived from the slope (cold air drains off the high ground) and the cluster is
    # seated partly by it - back to the hill, face to the water. But the seat has hard constraints
    # the wind does not: not below the drain, not on the hem, not off the canvas. When those rule
    # out every wind-facing margin, the settlement ends up with its back to the FIELD, and a belt
    # placed on the declared windward side is then planted in the rice - where `village_grove`
    # throws away almost every clump and the map fails both windbreak checks with a grove of eight
    # trees. Re-reading the exposure off the seat is the self-consistent answer and the true one: a
    # settlement's sheltered side is the side it actually turns its back to, and this map is
    # declaring which quarter that is. A GM who knows the region's real prevailing wind pins it on
    # the spec, and then the seat search is what bends instead.
    if plan.wind[0] * seat["out"][0] + plan.wind[1] * seat["out"][1] < 0.34:  # more than ~70 deg apart
        plan.windward = min(WIND_VECTORS, key=lambda q: -(WIND_VECTORS[q][0] * seat["out"][0] + WIND_VECTORS[q][1] * seat["out"][1]))
        s.M["meta"]["windward"] = plan.windward
    ax, ay = seat["along"]
    ox, oy = seat["out"]
    cx, cy = seat["cx"], seat["cy"]

    crops = crop_polys(s)

    def to_screen(p: Pt) -> Pt:
        """Seat frame (along the margin, away from the field) -> screen."""
        return (cx + ax * p[0] + ox * p[1], cy + ay * p[0] + oy * p[1])

    toe_now = s.toe_band() or None
    # THE SKELETON IS NO LONGER LAID HERE (feature 126). Its arms are drawn in `stage_lanes`,
    # after the houses exist, and are fitted to where the houses actually went. What survives in
    # this stage is the LAYOUT OBJECT ALONE, and only for its `gateway` - the downslope exit the
    # connector starts from. `skeleton_layout` is a pure function of (rolled knob, seat band), so
    # computing the gateway needs no houses and the connector's origin is unchanged by the move.
    #
    # THE RECORDED DEAD END ABOVE DOES NOT APPLY ANY MORE, and a reader who finds it in the git
    # history should know why. Feature 123 tried sizing the skeleton over the ground the houses
    # take and reverted it: longer arms offered the placer more frontage seats far from the
    # middle, and the cluster stretched to meet them. That was a FEEDBACK loop, and it existed
    # only because the skeleton was laid BEFORE the houses and its arms generated seats. Laid
    # afterwards there are no seats to generate, so the loop is severed rather than re-entered.
    layout = skeleton_layout(plan.lane_skeleton, 0.0, 0.0, seat["lat"], seat["dep"])
    # The spur no longer forks into the skeleton's arms, because they do not exist yet. It forks
    # into nothing and simply runs to the field; `stage_lanes` joins the network up afterwards.
    _kept_arms: list[tuple[Poly, Poly]] = []

    # the SPUR to the field: from the middle of the cluster to the nearest envelope point THE TRACK
    # CAN ACTUALLY REACH. Nearest-by-distance alone routes the path straight over the dry hem when
    # the hem lies between cluster and paddy - and a trodden path crosses no row crops
    # (`lanes_clear_of_dry_plots`; a real farm track runs on the baulk between plots, or round the
    # hem). So candidates are ordered by distance and the first one whose straight run is clear of
    # every hem plot wins; if none is, the nearest is used and the gate says so rather than the map
    # quietly shipping a lane through the barley.
    # A POLDER HAS NO FIELD SPUR. The valley hamlet's spur is a path from the cluster to the paddy's
    # edge, and it is meaningful there because the crop's margin is walkable ground. A polder is
    # ringed by its perimeter DIKE and, just inside that, the ring canal - so the way in is over the
    # dike at its sluice gaps, and a spur to the crop edge is a path to a bank. Drawn anyway it was
    # worse than pointless: every near target crosses the ring canal, so `path_violations` scored the
    # nearby vertices badly and the least-bad candidate ran from the cluster straight ACROSS the
    # block to a vertex on the far side (`fields_clear_of_road` on 4 of 12 cardinal polders).
    if plan.field_archetype == "polder_grid":
        s.M["meta"]["lane_skeleton"] = plan.lane_skeleton
        toe = s.toe_band()
        drawn_wet = [[(float(a), float(b)) for a, b in m["poly"]] for m in s.M.get("marshes", []) if m.get("role") != "defense" and m.get("poly")]
        gate_pt = push_out_of(plan.envelope, to_screen((float(layout["gateway"][0]), float(layout["gateway"][1]))), SPUR_SETBACK)
        track = connector_track(plan, gate_pt, avoid=[list(plan.envelope), *crops], wet=([toe] if toe else []) + drawn_wet, waters=drawn_water_segs(s))
        s.lane(route_around(plan.envelope, track, SPUR_SETBACK), width=6, clearance=LANE_CLEARANCE, worn=True, connector=True)
        return

    start = to_screen((0.0, 0.0))
    cen = centroid(plan.envelope)
    brook_segs = [(plan.sink_brook[i], plan.sink_brook[i + 1]) for i in range(len(plan.sink_brook) - 1)]

    def spur_path(target: Pt) -> Poly:
        # THE TIP STOPS OUTSIDE THE FIELD, measured on the LOCAL edge normal (GM 2026-08-12:
        # "Inashiro has village paths overlapping with rice paddies"). It used to pull back 8 px
        # along the SEAT's outward normal, which is one fixed direction for the whole map - so at a
        # target vertex whose own outline runs a different way, the pull-back was sideways and the
        # tip finished 28 px INSIDE the envelope, a track ending in the standing water. The normal
        # is taken from the two outline edges meeting at the target and oriented away from the
        # field's centroid, and the set-back covers the lane's own half-width plus the tolerance
        # `fields_clear_of_road` allows. A path stops AT the bund; the last few feet are the baulk.
        env = plan.envelope
        k = min(range(len(env)), key=lambda i2: math.hypot(env[i2][0] - target[0], env[i2][1] - target[1]))
        nx, ny = 0.0, 0.0
        for a2, b2 in ((env[k - 1], env[k]), (env[k], env[(k + 1) % len(env)])):
            ex, ey = unit(-(b2[1] - a2[1]), b2[0] - a2[0])
            nx, ny = nx + ex, ny + ey
        nx, ny = unit(nx, ny)
        if nx * (target[0] - cen[0]) + ny * (target[1] - cen[1]) < 0:
            nx, ny = -nx, -ny
        edge = (target[0] + nx * SPUR_SETBACK, target[1] + ny * SPUR_SETBACK)
        return [start, ((cx + edge[0]) / 2 + ax * 14, (cy + edge[1]) / 2 + ay * 14), edge]

    # ...and again the candidate is the DRAWN path, bow and all - see `path_is_clear`.
    spur = min(
        (spur_path(q) for q in sorted(plan.envelope, key=lambda v: math.hypot(v[0] - cx, v[1] - cy))),
        key=lambda p: (path_violations(p, crops, plan.sink_pond, brook_segs, plan.watercourses), polyline_len(p)),
    )
    _spur_pts = s.trim_off_marsh(clip_to_clear(spur, [*crops, *([toe_now] if toe_now else [])], 12.0))
    _spur_pts = _fork_spur(_spur_pts, _kept_arms)
    if len(_spur_pts) >= 2 and sum(math.dist(_spur_pts[k], _spur_pts[k + 1]) for k in range(len(_spur_pts) - 1)) > 20.0:
        s.lane(_spur_pts, width=5, clearance=LANE_CLEARANCE, worn=True)

    # the CONNECTOR, out to the frame
    # ...and the gate the connector starts FROM must itself be out of the crop. The skeleton's
    # gateway is a point in the seat frame, so on a cluster that sits against a concave stretch of
    # the fan it can land INSIDE the field envelope - and the connector then starts in the rice and
    # crosses the outline twice on its way out (Inashiro, GM 2026-08-12).
    gate = push_out_of(plan.envelope, to_screen((float(layout["gateway"][0]), float(layout["gateway"][1]))), SPUR_SETBACK)
    # THE TRACK LEAVES CLEAR OF THE WET TOE (GM 2026-08-12: "there's supposed to be a rule that
    # paths don't pass through marshland"). The marsh is not drawn until `stage_hinterland`, long
    # after this, so the router asks the ENGINE where it will be - `toe_band` is the same derivation
    # `hinterland()` lays the reeds on, factored out precisely so the two cannot disagree. With the
    # band in the obstacle list every straight-downslope bearing scores as a violation and the sweep
    # settles on a contour-following one, which is what a real valley track does anyway: roads run
    # ALONG the valley, they do not dive into the swamp at its foot.
    # ...and the wet ground is EVERY marsh, not just the toe band: the pond's reed fringe is drawn
    # back in `stage_sink`, before this, and a cohort sweep found ways ending in it on two maps.
    toe = s.toe_band()
    drawn_wet = [[(float(a), float(b)) for a, b in m["poly"]] for m in s.M.get("marshes", []) if m.get("role") != "defense" and m.get("poly")]
    track = connector_track(plan, gate, avoid=[list(plan.envelope), *crops], wet=([toe] if toe else []) + drawn_wet, waters=drawn_water_segs(s))
    s.lane(route_around(plan.envelope, track, SPUR_SETBACK), width=6, clearance=LANE_CLEARANCE, worn=True, connector=True)


def push_out_of(poly: Poly, p: Pt, margin: float) -> Pt:
    """Move `p` OUTSIDE `poly` by `margin`, on the normal of the outline EDGE nearest to it.

    Shared by the field spur's tip and the connector's route, which had the same defect for the same
    reason: both were pushed clear along one fixed map-wide direction (the seat's outward normal),
    which is only the right way out where the outline happens to run across it - so a spur tip
    finished 28 px inside the standing water. Projecting onto the nearest EDGE (not the nearest
    VERTEX - a point deep inside a lobe can have its nearest vertex right round the far side, and
    stepping out from there is a detour, not a fix) puts the way exactly where a track meeting a
    field goes: on the bund, just outside the crop. A point already clear is returned untouched, so
    this never drags a way back in."""
    ring = list(poly)
    n = len(ring)
    best: tuple[float, Pt, Pt, Pt] | None = None
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        q = seg_closest(p[0], p[1], a, b)
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        if best is None or d < best[0]:
            best = (d, q, a, b)
    assert best is not None  # a ring always has an edge
    d, q, a, b = best
    inside = point_in_poly(p[0], p[1], ring)
    if not inside and d > margin:
        return p
    nx, ny = unit(-(b[1] - a[1]), b[0] - a[0])
    cen = centroid(poly)
    if nx * (q[0] - cen[0]) + ny * (q[1] - cen[1]) < 0:
        nx, ny = -nx, -ny
    return (q[0] + nx * margin, q[1] + ny * margin)


def route_around(poly: Poly, path: Poly, margin: float, rounds: int = 6) -> Poly:
    """Bend a drawn way OUT of `poly` by walking its outline round the obstruction.

    `connector_track` sweeps forty bearings and keeps the LEAST-BAD when none is clean, which is the
    right call for a track that has to reach the frame somehow - but least-bad can still mean a leg
    cutting straight across a lobe of the fan, which is what the GM saw on Inashiro (2026-08-12).

    A track meeting a field GOES ROUND IT, and that is what this does literally: where a leg enters
    the outline at one edge and leaves at another, the outline's own vertices between those two
    edges are spliced in (the shorter way round), each stepped `margin` clear on its local normal.
    An earlier version inserted ONE waypoint at the mean of the crossings and re-ran; it converged a
    few pixels per round and ran out of rounds still crossing, because a point pushed off the middle
    of a lobe lands right beside the leg it came from. Following the boundary is both the correct
    detour and the one a farmer walks."""
    ring = list(poly)
    n = len(ring)
    out = [push_out_of(poly, q, margin) for q in path]
    for _ in range(rounds):
        redo: Poly = []
        cut = False
        for i in range(len(out) - 1):
            redo.append(out[i])
            a, b = out[i], out[i + 1]
            hits = [(k, h) for k in range(n) if segments_cross(a, b, ring[k], ring[(k + 1) % n]) and (h := seg_intersect(a, b, ring[k], ring[(k + 1) % n])) is not None]
            if len(hits) < 2:
                if (
                    hits
                ):  # pragma: no cover - a leg from outside to outside crosses a closed ring an EVEN number of times, so this is the guard for a leg grazing a vertex; no cohort map has produced one
                    redo.append(push_out_of(poly, hits[0][1], margin))
                    cut = True
                continue
            hits.sort(key=lambda kh: math.hypot(kh[1][0] - a[0], kh[1][1] - a[1]))
            k0, k1 = hits[0][0], hits[-1][0]
            fwd = [(k0 + 1 + t) % n for t in range((k1 - k0) % n)]
            bwd = [(k0 - t) % n for t in range((k0 - k1) % n)]
            way = fwd if len(fwd) <= len(bwd) else bwd
            redo += [push_out_of(poly, ring[t], margin) for t in way]
            cut = True
        redo.append(out[-1])
        out = redo
        if not cut:
            break
    return out


def clear_runs(
    pts: Poly,
    obstacles: Sequence[Poly],
    margin: float,
    step: float = 8.0,
    lines: Sequence[tuple[Pt, Pt]] = (),
    line_margin: float = 14.0,
    tight: Sequence[Poly] = (),
    tight_margin: float = 6.0,
    floor: float = 70.0,
) -> list[Poly]:
    """EVERY clear stretch of a polyline, not just the first or the longest - the through-lane
    counterpart of `clip_to_clear`.

    The difference is which end the blockage is allowed to cost you. `clip_to_clear` stops at the
    first ground the line may not cross, which is exactly right for a skeleton ARM: an arm radiates
    outward from the cluster, so everything past the blockage is beyond it anyway. A WEB lane is not
    an arm - it runs the length of the margin, and its two ends are just its two ends. Truncating it
    at the first fouled sample threw away the whole lane whenever the sampling happened to start in
    the crop, which is how Inashiro's back lanes came back as 250 ft of an intended 1400 while
    Sawada's alley spine - identical code, luckier starting end - survived at 719 ft. A lane does not
    cease to exist because the far end of the margin is under water.

    TWO OBSTACLE FAMILIES, because a web lane relates to them differently. `obstacles` is ground the
    lane may not go near at all - crop, marsh, the wet toe - and keeps the full `margin`. `tight` is
    the settlement's own fabric: houses, yards, gardens, groves. A lane threads BETWEEN those; it is
    the leftover room between two steadings, and holding it 20 ft off every wall would mean there is
    nowhere for it to be. So `tight` gets `tight_margin`, which is a hand's breadth.

    Returns every run that reaches `floor`, which defaults to the same 70 ft `clip_to_clear` uses.
    A short one is a real exception rather than a loosening: the footpath from an outlying steading's
    door to the nearest way is 60-odd feet by construction, and refusing it as a stub left eight
    houses unreachable while a path to each was being drawn and discarded. A back lane interrupted
    by a steading is two lanes, not one shortened one - and returning only the longest threw away
    ground that genuinely serves houses at the other end.

    A stub below the floor is not a lane, whichever way it was measured."""
    if not obstacles and not lines and not tight:
        return [list(pts)]

    # PREFILTER BY BOUNDING BOX BEFORE MEASURING ANYTHING. The web calls this hundreds of times per
    # map - once per candidate line, and again per dog-leg per target inside `_serve_stragglers` -
    # and each call was scanning every polygon in the settlement's whole fabric against every 4 ft
    # sample. That is the shape the skill's performance doctrine names outright: a per-candidate scan
    # of geometry that does not change during the scan. Unprefiltered it took a hamlet from ~15 s to
    # 45 s and broke a cohort worker outright. The box prunes; it never decides - a polygon whose
    # bounds cannot come within the margin cannot foul a sample, so dropping it changes no verdict.
    _lo_x = min(q[0] for q in pts)
    _hi_x = max(q[0] for q in pts)
    _lo_y = min(q[1] for q in pts)
    _hi_y = max(q[1] for q in pts)

    def _in_reach(o: Poly, m: float) -> bool:
        return not (max(q[0] for q in o) < _lo_x - m or min(q[0] for q in o) > _hi_x + m or max(q[1] for q in o) < _lo_y - m or min(q[1] for q in o) > _hi_y + m)

    obstacles = [o for o in obstacles if o and _in_reach(o, margin)]
    tight = [o for o in tight if o and _in_reach(o, tight_margin)]
    lines = [
        (a, b)
        for a, b in lines
        if not (max(a[0], b[0]) < _lo_x - line_margin or min(a[0], b[0]) > _hi_x + line_margin or max(a[1], b[1]) < _lo_y - line_margin or min(a[1], b[1]) > _hi_y + line_margin)
    ]

    def near(q: Pt, o: Poly, m: float) -> bool:
        return point_in_poly(q[0], q[1], list(o)) or min(seg_dist(q[0], q[1], o[j], o[(j + 1) % len(o)]) for j in range(len(o))) < m

    def fouled(q: Pt) -> bool:
        if any(seg_dist(q[0], q[1], a, b) < line_margin for a, b in lines):
            return True
        return any(near(q, o, margin) for o in obstacles) or any(near(q, o, tight_margin) for o in tight)

    samples: Poly = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        samples.extend((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1))
    runs: list[Poly] = []
    run: Poly = []
    for q in samples:
        if fouled(q):
            if len(run) >= 2 and polyline_len(run) >= floor:
                runs.append(run)
            run = []
            continue
        run.append(q)
    if len(run) >= 2 and polyline_len(run) >= floor:
        runs.append(run)
    return runs


def clip_to_clear(pts: Poly, obstacles: Sequence[Poly], margin: float, step: float = 8.0, lines: Sequence[tuple[Pt, Pt]] = (), line_margin: float = 14.0) -> Poly:
    """Shorten a polyline so it stops before the first ground it may not cross.

    Used on the cluster's lane arms. Dragging an offending VERTEX back toward the cluster was tried
    first and is not reliable: a vertex deep inside a large hem plot may not escape in the steps
    allowed, and it distorts the skeleton on the way. Truncating is both simpler and more honest -
    the lane ends where the crop begins, which is what a village lane does. Always returns at least
    a two-point line so the caller still has a lane."""
    if not obstacles and not lines:
        return pts

    def fouled(q: Pt) -> bool:
        if any(seg_dist(q[0], q[1], a, b) < line_margin for a, b in lines):
            return True
        return any(point_in_poly(q[0], q[1], list(o)) or min(seg_dist(q[0], q[1], o[j], o[(j + 1) % len(o)]) for j in range(len(o))) < margin for o in obstacles)

    out: Poly = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        run = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(run / step))
        last = a
        for k in range(1, n + 1):
            q = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
            if fouled(q):
                # NOTHING is returned if the surviving run is too short to be a lane. The first
                # version fell back to the ORIGINAL first segment here, which meant a lane blocked
                # immediately was drawn in full, unclipped - a fallback that does the opposite of
                # the function's job. A skeleton arm with nowhere to go is not drawn at all.
                trimmed = out + [last]
                return trimmed if polyline_len(trimmed) >= 70.0 else []
            last = q
        out.append(b)
    return out


def polyline_len(pts: Poly) -> float:
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def connector_track(plan: SitePlan, start: Pt, avoid: Sequence[Poly] = (), reach: float = 4000.0, wet: Sequence[Poly] = (), waters: Sequence[tuple[Pt, Pt]] = ()) -> Poly:
    """The track from the settlement's gateway to the map edge, steered clear of the crop.

    Bearings are tried outward from "away from the field, leaning downslope" - the direction a real
    track leaves by, since the wider world is downstream and the paddy is not walkable - and the
    first that reaches the frame without crossing the field envelope wins. Sweeping alternate sides
    at growing angles keeps the chosen bearing as close to the ideal as the geometry allows instead
    of jumping to whatever happens to be clear.

    The track is drawn PAST the canvas edge, not up to it: the gate wants an endpoint at the frame,
    and the crop is set later from the hard features, so a track that overshoots is trimmed by the
    viewBox while one that stops short reads as a dead end."""
    dx, dy = plan.fall
    ox, oy = plan.seat["out"]
    base = math.degrees(math.atan2(0.55 * oy + 0.85 * dy, 0.55 * ox + 0.85 * dx))
    # ...and clear of the POND. A track skirting the tameike ends up crossing the short drainage
    # ditch between field and pond at a very shallow angle, and an oblique crossing needs a much
    # longer deck than a square one - `bridges_span_their_water` caught exactly that, with an
    # abutment standing in the water. Steering around the pond removes the crossing instead of
    # widening the bridge, which is also what a real track does: you ford or bridge a ditch where it
    # is narrow and square, not where it fans into a reservoir.
    pond = plan.sink_pond
    brook = [(plan.sink_brook[i], plan.sink_brook[i + 1]) for i in range(len(plan.sink_brook) - 1)]
    # The planned net PLUS whatever water is actually drawn - the caller passes the streams, which
    # `plan.watercourses` does not carry and which nothing here used to test against.
    waters = [*plan.watercourses, *waters]
    # A FINE sweep, nearest bearing first. Sixteen coarse tries were enough when the only obstacle
    # was the field; with the pond and the drain brook added, a whole quadrant can be closed and a
    # coarse sweep steps straight over the gap between them - which drops through to the fallback,
    # and the fallback ignores every constraint. Forty bearings is a few hundred point tests.
    # The gateway can itself stand on hem ground when the cluster's back is partly hemmed, and a
    # start point inside a crop makes EVERY bearing fail - which is how the fallback below came to
    # fire at all. Step it clear first.
    start = pull_clear(start, (plan.seat["cx"], plan.seat["cy"]), avoid or [plan.envelope], 12.0)

    # A WET POLY IS SCORED WITH THE LANE'S WIDTH ON, not as a bare region (Cohort-41 2026-08-16).
    # `roads_clear_of_marsh` measures every marsh VERTEX against the way's CENTERLINE with the
    # way's half-width + 2 px of pad - so a track whose centerline clears the toe band's corner by
    # 4.5 px routes clean here and fails there. Inflating the polygon by 8 px (half the 6 px
    # connector lane + the gate's 2 px pad + 3 px slack) makes the router score the tread the gate
    # will measure, the same probe-measures-what-the-check-measures rule the bow comment below
    # states for the crop.
    def _inflated(w: Poly) -> Poly:
        wcx = sum(p[0] for p in w) / len(w)
        wcy = sum(p[1] for p in w) / len(w)
        out: Poly = []
        for wx, wy in w:
            wl = math.hypot(wx - wcx, wy - wcy) or 1.0
            out.append((wx + (wx - wcx) / wl * 8.0, wy + (wy - wcy) / wl * 8.0))
        return out

    wet_grown = [_inflated(w) for w in wet if len(w) >= 3]
    best: tuple[tuple[int, int], Poly] | None = None
    for swing in sorted((9.0 * k for k in range(-20, 21)), key=abs):
        theta = math.radians(base + swing)
        # THE CANDIDATE IS THE PATH THAT WILL BE DRAWN, not the straight line to its endpoint. A
        # foot track wanders, so the drawn polyline bows ~40 px either side of the bearing - and
        # testing the CHORD while drawing the BOW is how a track ended up crossing a hem plot and a
        # drainage ditch on maps whose straight line cleared both. (The skill's dev notes state the
        # rule in the label-probe case: a probe must measure what the check will measure. It applies
        # to routing just as squarely.)
        px, py = -math.sin(theta), math.cos(theta)
        path: Poly = [
            start,
            (start[0] + math.cos(theta) * reach * 0.18 + px * 34, start[1] + math.sin(theta) * reach * 0.18 + py * 34),
            (start[0] + math.cos(theta) * reach * 0.44 - px * 46, start[1] + math.sin(theta) * reach * 0.44 - py * 46),
            (start[0] + math.cos(theta) * reach, start[1] + math.sin(theta) * reach),
        ]
        # WET GROUND OUTRANKS EVERYTHING ELSE (GM 2026-08-12). The toe marsh is a contour band
        # spanning the whole canvas below the crop, so on a map whose cluster sits in a pocket of
        # the fan NO bearing is clean of both - and a single violation count lets one crop clip
        # outweigh a thousand feet of swamp. Scoring them separately, wet first, makes the sweep
        # leave along the contour and exit the frame ABOVE the marsh, which is what a real valley
        # road does; whatever crop it then clips is bent round afterwards by `route_around`, which
        # the marsh has no equivalent of because a track through a marsh cannot be nudged dry.
        soaked = sum(path_violations(path, [w], None, ()) for w in wet_grown)  # the WET POLYGON only - pond and brook are scored once, below
        violations = path_violations(path, avoid or [plan.envelope], pond, brook, waters)
        if soaked == 0 and violations == 0:
            return path
        if best is None or (soaked, violations) < best[0]:
            best = ((soaked, violations), path)
    # NO CLEAN BEARING: take the LEAST-BAD one rather than a fixed escape route.
    #
    # This used to return `start` plus a ray straight away from the field, and that fallback is what
    # actually shipped the defect: it consulted nothing, so on any map where the sweep came up empty
    # the connector was drawn through the hem and across the drainage ditch, failing three checks at
    # once. A fallback that ignores the constraints is worse than no fallback, because it looks like
    # a decision. Scoring every candidate and keeping the best means a hard map degrades by one
    # crossing instead of by everything.
    assert best is not None
    return best[1]


def stream_segs(s: Settlement) -> list[tuple[Pt, Pt]]:
    """Just the STREAMS - the water a way needs a real deck to cross, as opposed to a plank.

    SPLIT OUT FROM `drawn_water_segs` BECAUSE THE DISTINCTION IS LOAD-BEARING, and it was measured
    the hard way. A peer session wired a blanket `shallow_crossing` veto into the link pass against
    the undifferentiated list (`plan.watercourses` plus every drawn channel) and the cohort went
    **41/48 -> 26/48, with 21 seeds failing `farmhouses_reach_a_way`**. The cause was the LIST, not
    the placement: a link joining two halves of a hamlet crosses field ditches constantly and often
    obliquely, and an aze ditch is a stride across - demanding a square crossing of every one strands
    the very components the pass exists to join. A far bigger defect than the oblique stream crossing
    the veto was written for.

    So the rule a way must respect is not "never cross water at a slant", it is "never cross water
    that needs a DECK at a slant", and this is that subset. `drawn_water_segs` still returns
    everything, for callers that want to avoid or bridge any water at all.

    Consumer note: `_join_orphan_ways` is the pass that needs this - it deliberately passes an EMPTY
    water list today ("a link may go the long way round, and may be planked"), which is exactly why
    it is the pass that can lay a way down the length of a brook (cohort seed 47).
    `_bridge_collinear_breaks` does NOT: it hands its water to `_route`, which already refuses to
    cross a watercourse at any angle, so a veto there would be unreachable code."""
    return [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for st in s.M.get("streams", []) if st.get("poly") for a, b in zip(st["poly"], st["poly"][1:], strict=False)]


def drawn_water_segs(s: Settlement) -> list[tuple[Pt, Pt]]:
    """Every DRAWN watercourse on the map, as segments - channels AND streams.

    THE STREAMS WERE MISSING FROM EVERY WAY-VS-WATER TEST, and that is the whole reason this helper
    exists rather than the inline `drawn_channels` comprehension it replaces. `drawn_channels` holds
    the irrigation net; `M["streams"]` holds the feed brook and any natural course, and nothing in
    this module ever looked at it. So `shallow_crossing` - which exists, is correct, and is wired
    into `path_violations` - simply never saw the brook: on cohort seed 47 a connector crossed a
    7 px stream at 17 degrees, and `bridges_span_their_water` failed the deck it produced, with the
    guard that was written for exactly that case sitting one list away.

    Same family as this engine's recurring defect - a guard keyed on the wrong input measures
    something other than what it protects. `trades.py` already reads both records together; this is
    that pattern, applied where the ways are laid."""
    segs = [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for rec in s.M.get("drawn_channels", []) for a, b in zip(rec["pts"], rec["pts"][1:], strict=False)]
    return segs + stream_segs(s)  # ONE definition of what a stream is, shared with the deck-needing subset


def path_violations(path: Poly, avoid: Sequence[Poly], pond: tuple[float, float, float, float] | None, brook: Sequence[tuple[Pt, Pt]], waters: Sequence[tuple[Pt, Pt]] = ()) -> int:
    """How many segments of a drawn way foul the crop, the pond or the drain brook (0 = clear).

    A COUNT rather than a boolean, so a caller with no clean option can still take the least-bad one.

    The pond and the brook are avoided outright rather than bridged: a way meeting water at a
    shallow angle needs a far longer deck than a square crossing, and `bridges_span_their_water`
    measures the deck the engine actually drew. Going around removes the crossing entirely, which
    is also what a real track does - you ford a ditch where it is narrow and square."""
    bad = 0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        if (
            (pond is not None and crosses_disc(a, b, (pond[0], pond[1]), max(pond[2], pond[3]) + 80.0))
            or any(seg_intersect(a, b, p, q) is not None for p, q in brook)
            or any(crosses_poly(a, b, poly) for poly in avoid)
            or any(shallow_crossing(a, b, p, q) for p, q in waters)
            or any(crossing_lands_on_crop(a, b, p, q, avoid) for p, q in waters)
        ):
            bad += 1
    # ...and a way may not bridge TWICE within a deck's length. `s.bridges()` decks every crossing
    # it finds, so a way cutting two ditches a few tens of px apart gets two decks drawn on top of
    # each other - which `features_do_not_overlap` reads as a ('bridges', 'bridges') pair, and which
    # is a drawing error rather than a siting one. Crossing further along, where the ditches have
    # separated, is what a track does anyway.
    hits = [x for i in range(len(path) - 1) for p, q in waters if (x := seg_intersect(path[i], path[i + 1], p, q)) is not None]
    bad += sum(1 for i, u in enumerate(hits) for v in hits[i + 1 :] if math.hypot(u[0] - v[0], u[1] - v[1]) < 46.0)
    return bad


def crossing_lands_on_crop(a: Pt, b: Pt, p: Pt, q: Pt, crops: Sequence[Poly], pad: float = 14.0) -> bool:
    """Does the way a->b meet the watercourse p->q at a point standing on cropland?

    A crossing gets a DECK, and a deck laid on a hem plot is a bridge across the barley
    (`features_do_not_overlap` reports it as a dry_plots/bridges pair). The way is free to cross the
    same ditch a little further along where the crop stops - which is where the bund is anyway."""
    hit = seg_intersect(a, b, p, q)
    if hit is None:
        return False
    return any(point_in_poly(hit[0], hit[1], list(c)) or min(seg_dist(hit[0], hit[1], c[i], c[(i + 1) % len(c)]) for i in range(len(c))) < pad for c in crops)


def shallow_crossing(a: Pt, b: Pt, p: Pt, q: Pt, limit_deg: float = 42.0) -> bool:
    """Does the way a->b cross the watercourse p->q at a SHALLOW angle?

    A way is allowed to cross an irrigation ditch - that is what a plank or a small timber bridge is
    for, and forbidding it outright would cut the field spur off from the field. What it may not do
    is cross at a slant: an oblique crossing needs a deck of (width + deck_w x |cos|) / sin plus a
    landing each side, so `bridges_span_their_water` fails it with an abutment standing in the
    water. Steering the way to meet the ditch square is the fix a farmer would recognize."""
    if seg_intersect(a, b, p, q) is None:
        return False
    ux, uy = unit(b[0] - a[0], b[1] - a[1])
    vx, vy = unit(q[0] - p[0], q[1] - p[1])
    return abs(math.degrees(math.asin(max(-1.0, min(1.0, ux * vy - uy * vx))))) < limit_deg
