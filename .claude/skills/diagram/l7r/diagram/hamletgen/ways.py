"""STAGE 4b: the lanes, the connector track, and what makes a path legal.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from l7r.diagram.settlement import Settlement, point_in_poly, rot_rect, seg_closest, seg_dist, seg_intersect, segments_cross, skeleton_layout, web_cuts
from l7r.diagram.sitegen.geom import centroid, crop_polys, crosses_disc, crosses_poly, pull_clear, unit

from .cluster import _arm_crossing_accidental, _fork_spur, seat_cluster
from .consts import BUNDLE_PITCH, CLUSTER_SPAN_FACTOR, LANE_CLEARANCE, MIN_WEB_GAP, SPUR_SETBACK, WEB_CLEARANCE, WEB_FABRIC_GAP, WEB_REACH_FT, WIND_VECTORS, Poly, Pt
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
            return abs((q[0] - anchor[0]) * ax + (q[1] - anchor[1]) * ay) <= span

        n_env = len(env)
        look = 12

        def worth_continuing(i: int, step: int) -> bool:
            return any(close_enough(env[(i + step * k) % n_env]) for k in range(1, look + 1))

        start = min(range(n_env), key=lambda i: math.dist(env[i], (seat["cx"], seat["cy"])))
        lo = start
        while (start - lo) < n_env - 1 and worth_continuing(lo, -1):
            lo -= 1
        hi = start
        while (hi - start) < n_env - 1 and worth_continuing(hi, +1):
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
    for key in ("village_groves", "commons"):
        out.extend(([(float(a), float(b)) for a, b in rec["poly"]], None, key) for rec in s.M.get(key, []) if rec.get("poly"))
    for w in s.M.get("wells", []):
        r = float(w.get("r", 8.0))
        out.append(([(float(w["x"]) + r * c, float(w["y"]) + r * sn) for c, sn in ((1, 0), (0, 1), (-1, 0), (0, -1))], None, "wells"))
    for key in ("farm_sheds", "byres"):
        for r in s.M.get(key, []):
            own = r.get("of")
            out.append((rot_rect(float(r["x"]), float(r["y"]), float(r["w"]), float(r["h"]), float(r.get("rot", 0.0))), (float(own[0]), float(own[1])) if own else None, key))
    return out


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
    alley IS the residual gap between two plots, "colonised as semi private space by the adjoining
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
        for cut in web_cuts(stands, WEB_REACH_FT, MIN_WEB_GAP):
            a0, a1 = _extent(cut, arcs, stands)
            n = max(4, int((a1 - a0) / 40.0))
            lines.append([frame(a0 + (a1 - a0) * i / n, cut) for i in range(n + 1)])

    crops = crop_polys(s)
    toe = s.toe_band() or None
    wet = [[(float(a), float(b)) for a, b in m["poly"]] for m in s.M.get("marshes", []) if m.get("role") != "defense" and m.get("poly")]
    hard = [list(plan.envelope), *crops, *([toe] if toe else []), *wet]
    fabric = _homestead_polys(s)
    walls = [poly for poly, _, _ in fabric]
    drawn_water = [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for rec in s.M.get("drawn_channels", []) for a, b in zip(rec["pts"], rec["pts"][1:], strict=False)]
    for line in lines:
        # FINER SAMPLING AND A WIDER FABRIC MARGIN THAN THE DEFAULTS. A web lane runs among the
        # steadings rather than past them, so it gets many more chances to clip a corner: sampled
        # every 8 ft with a 6 ft margin it cut across dooryard gardens on 7 of 24 cohort seeds, both
        # endpoints of the offending step legally clear while the step between them crossed the bed.
        # 4 ft samples and an 8 ft margin close that; the cost is sampling time on a short line.
        for run in clear_runs(line, hard, 20.0, step=4.0, lines=list(plan.watercourses) + drawn_water, tight=walls, tight_margin=WEB_FABRIC_GAP):
            _lay_web_lane(s, run, hard, walls, list(plan.watercourses) + drawn_water)
    # A WEB LANE STOPS WHERE IT STOPS SERVING. Clipping ends an arm wherever the crop or a steading
    # happens to begin, which can leave a tail running on into bare grass - `lanes_reach_something`
    # is right to call that a tread that serves nobody. The engine already owns this trim; the web
    # simply has to ask for it after adding to the network.
    s.trim_lane_stubs()
    # STRAGGLERS COME AFTER THE TRIM, NEVER BEFORE IT. `trim_lane_stubs` drops any lane under its
    # 71 ft minimum, and a footpath from a door to the nearest way is about 65 ft by construction -
    # so run the other way round, every spur this pass drew was silently deleted again and the eight
    # unreached houses stayed exactly eight. A door path is short on purpose; it is not a stub.
    _serve_stragglers(s, plan, hard, fabric, list(plan.watercourses) + drawn_water)
    s.M["meta"]["lane_web"] = plan.lane_web


# How near a footpath's far end must come to an existing way to count as joining it. This is
# `lanes_reach_something`'s own way-reach, deliberately: a path that gets this close IS connected as
# far as the gate is concerned, and demanding better only threw away paths that served their house.
_LANE_JOIN_FT = 30.0  # inside lanes_reach_something's own 40 ft, with room to spare for a rounded end


def _reach(c: Pt, path: Poly) -> float:
    """How near a polyline comes to a point - the same measurement `farmhouses_reach_a_way` makes."""
    return min(math.dist(c, seg_closest(c[0], c[1], a, b)) for a, b in zip(path, path[1:], strict=False))


def _clear_link(a: Pt, b: Pt, hard: list[Poly], walls: Sequence[Poly], water: list[tuple[Pt, Pt]]) -> bool:
    """Is the short run between two points walkable? Used before extending a lane end onto the way
    it meets, so a junction is drawn as a touch without the touch crossing anything."""
    if math.dist(a, b) < 1.0:
        return True
    runs = clear_runs([a, b], hard, 20.0, step=3.0, lines=water, tight=walls, tight_margin=WEB_FABRIC_GAP, floor=0.5)
    return bool(runs) and _reach(a, runs[0]) < 3.0 and _reach(b, runs[0]) < 3.0


def _net_segs(s: Settlement) -> list[tuple[Pt, Pt]]:
    """Every drawn way on the map right now, as segments."""
    return [((float(p[0]), float(p[1])), (float(q[0]), float(q[1]))) for ln in s.M.get("lanes", []) for p, q in zip(ln["pts"], ln["pts"][1:], strict=False)]


def _lay_web_lane(s: Settlement, run: Poly, hard: list[Poly], walls: list[Poly], water: list[tuple[Pt, Pt]]) -> bool:
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
    if segs:
        shadowed = sum(1 for q in run if min(seg_dist(q[0], q[1], a, b) for a, b in segs) < MIN_WEB_GAP)
        if shadowed > 0.6 * len(run):
            return False
        d0 = min(seg_dist(run[0][0], run[0][1], a, b) for a, b in segs)
        d1 = min(seg_dist(run[-1][0], run[-1][1], a, b) for a, b in segs)
        end = 0 if d0 <= d1 else -1
        gap = min(d0, d1)
        p = run[end]
        q = min((seg_closest(p[0], p[1], a, b) for a, b in segs), key=lambda z: math.dist(p, z))
        if gap > _LANE_JOIN_FT:
            if math.dist(p, q) > WEB_REACH_FT * 2.0:
                return False
            link = [r for r in clear_runs([p, q], hard, 20.0, step=4.0, lines=water, tight=walls, tight_margin=WEB_FABRIC_GAP, floor=12.0) if _reach(p, r) < 12.0 and _net_reach(r, segs) < 12.0]
            if not link:
                return False
            s.lane(link[0], width=3, clearance=WEB_CLEARANCE, worn=True)
            s.M["lanes"][-1]["web"] = True
        elif _clear_link(run[end], q, hard, walls, water):
            # SNAP ONLY IF THE GROUND BETWEEN IS CLEAR. Extending an end onto the way it meets is
            # what makes the junction read as a touch instead of a gap - but the few feet being
            # added are ground like any other, and adding them blind put lane ink across houses and
            # garden beds (`features_do_not_overlap`, `houses_clear_of_lanes` on every cohort seed
            # the moment snapping went in). If the gap is not walkable the lane simply ends where it
            # ended; a visible break is better than a lane through a wall.
            run = ([q, *run]) if end == 0 else ([*run, q])
    s.lane(run, width=3, clearance=WEB_CLEARANCE, worn=True)
    # Flagged so `lane_frontage` does not offer seats along it. A web lane is SERVICE - it threads
    # behind and between the steadings - and inviting new houses onto the way that exists to reach
    # the old ones is how the cluster starts sprawling again.
    s.M["lanes"][-1]["web"] = True
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
            if min(math.dist(c, seg_closest(c[0], c[1], a, b)) for a, b in segs) <= WEB_REACH_FT:
                continue
            # Everything EXCEPT this steading's own house, yard, garden and shed - the path has to
            # be able to leave its own dooryard, and `of` says which features those are.
            # ONLY THE HOUSE ITSELF STEPS ASIDE - not its yard, not its garden. The path has to be
            # able to start at the door, which is why the house is excluded at all; everything else
            # the steading owns is ground the overlap matrix will not let a lane cross, and each
            # relaxation was tried and measured. Excluding the whole bundle put spurs through their
            # own garden beds (7 of 24 cohort seeds, `lanes` vs `gardens`); excluding the yard as
            # well put them across the threshing floor (`lanes` vs `threshing_yards`). The
            # dog-legs below are what finds a way out that does not need any of those exemptions.
            others = [poly for poly, owner, kind in fabric if owner is None or math.dist(owner, c) > 1.0 or kind != "houses"]
            step = math.hypot(float(h["w"]), float(h["h"])) / 2 + 8.0
            # EVERY WAY WITHIN REACH IS A CANDIDATE, not merely the closest one. A path aimed at the
            # nearest lane can run the length of a neighbor's threshing yard and be refused for its
            # whole run, while a way ten feet further off is reachable across open ground - measured,
            # that was every one of the eight houses this pass was failing to serve. Real footpaths
            # go where there is room, so the candidates are tried nearest-first and the first one
            # that has room wins.
            targets = sorted((seg_closest(c[0], c[1], a, b) for a, b in segs), key=lambda q: math.dist(c, q))
            for tgt in targets[:60]:
                # The radius is generous on purpose. A steading the web could not reach is by
                # definition one whose nearest way is already beyond the reach, so a search bounded
                # at twice the reach gave up on exactly the houses that needed it - two of seed 3's,
                # at 171 and 201 ft, were never attempted at all. A long path is a real thing on the
                # edge of a hamlet; a house with no path is not.
                if math.dist(c, tgt) > WEB_REACH_FT * 3.5:
                    break
                dx, dy = unit(tgt[0] - c[0], tgt[1] - c[1])
                door = (c[0] + dx * step, c[1] + dy * step)
                # A FOOTPATH BENDS. The straight run is tried first and is usually right, but a path
                # that meets a neighbor's garden bed head-on should go round it rather than be
                # abandoned - which is what a person does, and abandoning it was the single biggest
                # residue left in the cohort once the overlaps were fixed. The dog-legs are one
                # waypoint pushed off the straight line, nearest offsets first, so a straight path
                # always wins when it exists and the bend is only as much as it has to be.
                mid = ((door[0] + tgt[0]) / 2, (door[1] + tgt[1]) / 2)
                px, py = -dy, dx
                cands = [[door, tgt]]
                cands += [[door, (mid[0] + px * off, mid[1] + py * off), tgt] for k in (40.0, 80.0, 130.0) for off in (k, -k)]
                hit: list[Poly] = []
                for cand in cands:
                    runs = clear_runs(cand, hard, 20.0, step=4.0, lines=water, tight=others, tight_margin=WEB_FABRIC_GAP, floor=20.0)
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
                    # reach the network; and its length may not exceed 1.6x its own chord, which is
                    # the band every honest way on these maps already sits in (1.00-1.34).
                    hit = [r for r in runs if _reach(c, r) <= step + 14.0 and _net_reach(r, segs) <= _LANE_JOIN_FT and polyline_len(r) <= 1.6 * max(math.dist(r[0], r[-1]), 1.0)]
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
                    path = list(hit[0])
                    join = min((seg_closest(path[-1][0], path[-1][1], a, b) for a, b in segs), key=lambda z: math.dist(path[-1], z))
                    if _clear_link(path[-1], join, hard, others, water):
                        path = [*path, join]
                    door_at = (c[0] + dx * step * 0.6, c[1] + dy * step * 0.6)
                    if _clear_link(path[0], door_at, hard, others, water):
                        path = [door_at, *path]
                    s.lane(path, width=3, clearance=WEB_CLEARANCE, worn=True)
                    s.M["lanes"][-1]["web"] = True
                    added += 1
                    break
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
    # ...and every marsh ALREADY DRAWN - on a polder the header reservoir's reed fringe is laid in
    # `stage_polder`, before the ways, and a lane arm ran straight through it.
    wet_now = [[(float(a), float(b)) for a, b in m["poly"]] for m in s.M.get("marshes", []) if m.get("role") != "defense" and m.get("poly")]
    # The skeleton is laid over the SEAT BAND, unchanged. Sizing it over the wider ground the houses
    # take was tried (feature 123) and reverted: longer arms give the placer more frontage seats far
    # from the middle, and the cluster stretches to meet them. Reaching the outlying houses is the
    # LANE WEB's job, and the web is laid after they exist - see `stage_web`.
    layout = skeleton_layout(plan.lane_skeleton, 0.0, 0.0, seat["lat"], seat["dep"])
    _raw_arms = [[to_screen((p[0], p[1])) for p in lane_pts] for lane_pts in layout["lanes"]]

    _kept_arms: list[tuple[Poly, Poly]] = []
    for _ai, lane_pts in enumerate(layout["lanes"]):
        # ...pulled back out of any hem plot the arm would otherwise reach into. The skeleton is
        # sized from the household count, so on a cluster seated tight against the hem a `cross`
        # crossbar can overrun into the barley - and a lane may touch a plot's edge but never cross
        # its interior. Shortening the arm is the honest fix: the lane simply ends where the crop
        # starts, which is what a village lane does.
        # The arms are clipped at WATER as well as at crop. A cluster's internal lanes serve the
        # houses; they have no business crossing a ditch, and a lane that does gets a deck from
        # `s.bridges()` sized for the angle it happens to meet the water at - which on a slant comes
        # up short (`bridges_span_their_water`). The spur and the connector are the ways that leave,
        # and they are routed to meet water squarely; an arm just stops at the bank.
        # ...clipped against the DRAWN water lines as well as the recorded ones: `field_channel`
        # fillets its polyline before drawing it, and a bridge is decked on what was drawn.
        drawn_water = [((float(a[0]), float(a[1])), (float(b[0]), float(b[1]))) for rec in s.M.get("drawn_channels", []) for a, b in zip(rec["pts"], rec["pts"][1:], strict=False)]
        # ...and the WET TOE is clipped against like any other ground a lane may not cross, not just
        # trimmed at the ends: `trim_off_marsh` walks an END back, which is the right move for a way
        # that pokes into the reeds, but an arm whose MIDDLE runs through them needs the truncation
        # its own docstring points at. An arm ends where the marsh begins - that is what a lane does.
        # ...and the WET field too, not only the dry plots. `crop_polys` returns `dry_plots`, so a
        # lane arm was never clipped against the paddy itself - invisible on a valley map, where the
        # cluster sits on a margin and the arms point away from the fan, and immediate on a POLDER,
        # where the block lies right beside the village and an arm reached into the rice. The
        # connector has always listed the envelope; the arms simply never did.
        arm = clip_to_clear([to_screen((p[0], p[1])) for p in lane_pts], [list(plan.envelope), *crops, *([toe_now] if toe_now else []), *wet_now], 20.0, lines=list(plan.watercourses) + drawn_water)
        arm = s.trim_off_marsh(arm)  # ...and off the pond's reed fringe, which is already drawn by now
        if len(arm) >= 2:
            if _arm_crossing_accidental(arm, _raw_arms[_ai], _kept_arms):
                continue  # pragma: no cover - no rolled map currently trips the drop; the decision logic is unit-tested via _arm_crossing_accidental
            _kept_arms.append((arm, _raw_arms[_ai]))
            s.lane(arm, width=5, clearance=LANE_CLEARANCE, worn=True)
    s.M["meta"]["lane_skeleton"] = plan.lane_skeleton

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
        track = connector_track(plan, gate_pt, avoid=[list(plan.envelope), *crops], wet=([toe] if toe else []) + drawn_wet)
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
    track = connector_track(plan, gate, avoid=[list(plan.envelope), *crops], wet=([toe] if toe else []) + drawn_wet)
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


def connector_track(plan: SitePlan, start: Pt, avoid: Sequence[Poly] = (), reach: float = 4000.0, wet: Sequence[Poly] = ()) -> Poly:
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
    waters = plan.watercourses
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
