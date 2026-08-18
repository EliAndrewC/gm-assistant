"""STAGE 4b: the lanes, the connector track, and what makes a path legal.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from l7r.diagram.settlement import Settlement, point_in_poly, seg_closest, seg_dist, seg_intersect, segments_cross, skeleton_layout, web_lanes
from l7r.diagram.sitegen.geom import centroid, crop_polys, crosses_disc, crosses_poly, pull_clear, unit

from .cluster import _arm_crossing_accidental, _fork_spur, seat_cluster
from .consts import BUNDLE_PITCH, CLUSTER_SPAN_FACTOR, LANE_CLEARANCE, SPUR_SETBACK, WEB_CLEARANCE, WIND_VECTORS, Poly, Pt
from .plan import SitePlan


class _margin_frame:  # noqa: N801 - used as a callable coordinate map, not as a type
    """OUTLINE COORDINATES for the stretch of field margin this cluster fronts.

    `f(arc, standoff)` maps a point given as (distance walked along the field edge, distance out
    from it) to screen. It is the same walk `front_row` makes - the outline vertices within the
    cluster's lateral reach, ordered along the margin, each offset outward on the local normal - and
    it exists for the same reason: the margin CURVES, so anything meant to run parallel to the field
    has to be built on the edge itself rather than ruled straight across it.

    Read `.arc` for the total length of that stretch, which is the domain the web is laid over."""

    def __init__(self, plan: SitePlan, span: float) -> None:
        env, seat = plan.envelope, plan.seat
        ax, ay = seat["along"]
        cen = centroid(env)
        # ONLY THE SIDE THE CLUSTER IS ON. The envelope is a closed ring, so the along-axis test
        # alone admits the vertices DIRECTLY OPPOSITE too - and the arc then snakes down one flank
        # of the fan, round the end and back up the other. Measured on Sawada: 3,060 ft of "margin"
        # for a cluster 808 ft long, which over-generated laterals more than three to one and laid
        # them where no house stands (`lanes_reach_something`). `front_row` gets away without this
        # test because its caller drops any seat outside the band; the web has no such backstop, so
        # it makes the test itself. The side is read off the seat's own outward normal, which is the
        # direction the settlement lies in from the field.
        ox_, oy_ = seat["out"]
        cen0 = centroid(env)
        pts = [
            p
            for p in env
            if abs((p[0] - seat["anchor"][0]) * ax + (p[1] - seat["anchor"][1]) * ay) <= span and (p[0] - cen0[0]) * ox_ + (p[1] - cen0[1]) * oy_ > 0.0
        ]
        pts.sort(key=lambda p: (p[0] - seat["anchor"][0]) * ax + (p[1] - seat["anchor"][1]) * ay)
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
    # THE SKELETON IS SIZED OVER THE GROUND THE HOUSES ACTUALLY TAKE, not over the seat band.
    #
    # `front_row` samples the outline out to `lat * CLUSTER_SPAN_FACTOR`, so the cluster is 1.6x
    # longer than the band - and this call used to pass the bare `lat`. The lanes therefore huddled
    # in the middle of the cluster and the houses at its two ends had nothing near them: 25 of the
    # four pool hamlets' 66 farmhouses stood more than 120 ft from any way, every one of them at a
    # large offset ALONG the long axis. One constant, read by both, is the fix.
    _span = seat["lat"]
    layout = skeleton_layout(plan.lane_skeleton, 0.0, 0.0, _span, seat["dep"])
    # ...plus the LANE WEB, which is what actually discharges the obligation that every farmhouse be
    # reachable (research/homesteads.md; constitution Principle XII). Its FORM is the rolled knob -
    # `alleys` (a spine with laterals between the plots; the place grew) or `back_lane` (lanes
    # parallel to the margin, one fronting the field and one behind the plots; the place was laid
    # out). Web arms are appended to the skeleton's own and go through the identical clip-and-trim
    # path below, so they obey every rule an arm obeys: out of the crop, off the wet toe, off the
    # marsh, and stopping at a watercourse rather than crossing it.
    # Both families arrive in SCREEN coordinates here, from two different frames: the skeleton is
    # laid in the seat frame (straight arms across a straight band) and the web in outline
    # coordinates (arc along the margin, standoff out from the field edge), because a lane that runs
    # PARALLEL to the field has to follow its curve or the clip cuts it to a stub.
    _margin = _margin_frame(plan, _span)
    _lanes = [([to_screen((p[0], p[1])) for p in lane_pts], False) for lane_pts in layout["lanes"]]
    _lanes += [([_margin(p[0], p[1]) for p in _w], True) for _w in web_lanes(plan.lane_web, _margin.arc, seat["dep"] * 2.0, BUNDLE_PITCH, LANE_CLEARANCE)]
    s.M["meta"]["lane_web"] = plan.lane_web
    _raw_arms = [list(lane_pts) for lane_pts, _ in _lanes]

    _kept_arms: list[tuple[Poly, Poly]] = []
    for _ai, (lane_pts, _is_web) in enumerate(_lanes):
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
        # A WEB lane keeps its longest clear RUN; a skeleton arm stops at the first blockage. See
        # `longest_clear_run` for why the two ways of losing ground are not interchangeable.
        _clip = longest_clear_run if _is_web else clip_to_clear
        arm = _clip(list(lane_pts), [list(plan.envelope), *crops, *([toe_now] if toe_now else []), *wet_now], 20.0, lines=list(plan.watercourses) + drawn_water)
        arm = s.trim_off_marsh(arm)  # ...and off the pond's reed fringe, which is already drawn by now
        if len(arm) >= 2:
            if _arm_crossing_accidental(arm, _raw_arms[_ai], _kept_arms):
                continue  # pragma: no cover - no rolled map currently trips the drop; the decision logic is unit-tested via _arm_crossing_accidental
            _kept_arms.append((arm, _raw_arms[_ai]))
            # A WEB LANE IS NARROW, AND ITS CORRIDOR IS NARROW TOO. `LANE_CLEARANCE` is the setback
            # for a lane the homesteads FRONT - it holds a minka's drawn footprint plus its dooryard
            # off the tread. The web is not that: the sources describe "narrow lanes and alleys",
            # with the lateral ones "colonised as semi private space by the adjoining house", which
            # is a way you build right up to. Given the 40 ft corridor instead, the web ate the
            # middle of the cluster and shoved the houses outward - the four hamlets' long axes went
            # 808 -> 1220, 716 -> 1131, 994 -> 1144 and 518 -> 1022 ft, which is the opposite of
            # nucleation and would have been a silent regression, since no check measures sprawl.
            _w, _c = (3, WEB_CLEARANCE) if _is_web else (5, LANE_CLEARANCE)
            s.lane(arm, width=_w, clearance=_c, worn=True)
            # A WEB LANE IS SERVICE, NOT FRONTAGE. `lane_frontage` offers seats along both verges of
            # every internal lane, so the web - which exists to REACH the houses - was also inviting
            # more houses, and the cluster grew to meet it: the four hamlets' long axes went 808 ->
            # 1220, 716 -> 1131, 994 -> 1144 and 518 -> 1022 ft, which is the opposite of nucleation.
            # A back lane runs behind the plots and an alley is the residual gap between them;
            # neither is a street you build a new farmhouse onto. Flagged like the connector, and
            # skipped by `lane_frontage` for the same reason: some ways are not building ground.
            if _is_web:
                s.M["lanes"][-1]["web"] = True
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


def longest_clear_run(pts: Poly, obstacles: Sequence[Poly], margin: float, step: float = 8.0, lines: Sequence[tuple[Pt, Pt]] = (), line_margin: float = 14.0) -> Poly:
    """The longest UNBROKEN clear stretch of a polyline - the through-lane counterpart of
    `clip_to_clear`.

    The difference is which end the blockage is allowed to cost you. `clip_to_clear` stops at the
    first ground the line may not cross, which is exactly right for a skeleton ARM: an arm radiates
    outward from the cluster, so everything past the blockage is beyond it anyway. A WEB lane is not
    an arm - it runs the length of the margin, and its two ends are just its two ends. Truncating it
    at the first fouled sample threw away the whole lane whenever the sampling happened to start in
    the crop, which is how Inashiro's back lanes came back as 250 ft of an intended 1400 while
    Sawada's alley spine - identical code, luckier starting end - survived at 719 ft. A lane does not
    cease to exist because the far end of the margin is under water.

    Returns [] if no clear run reaches the same 70 ft floor `clip_to_clear` uses: a stub is not a
    lane, whichever way it was measured."""
    if not obstacles and not lines:
        return pts

    def fouled(q: Pt) -> bool:
        if any(seg_dist(q[0], q[1], a, b) < line_margin for a, b in lines):
            return True
        return any(point_in_poly(q[0], q[1], list(o)) or min(seg_dist(q[0], q[1], o[j], o[(j + 1) % len(o)]) for j in range(len(o))) < margin for o in obstacles)

    samples: Poly = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        samples.extend((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1))
    best: Poly = []
    run: Poly = []
    for q in samples:
        if fouled(q):
            run = []
            continue
        run.append(q)
        if polyline_len(run) > polyline_len(best):
            best = list(run)
    return best if len(best) >= 2 and polyline_len(best) >= 70.0 else []


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
