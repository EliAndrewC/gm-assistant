"""STAGE 3: where the runoff goes - the drain and the tameike it feeds.

Split from hamletgen.py by feature 111; bodies verbatim. See hamletgen/CLAUDE.md.
"""

from __future__ import annotations

import math

from settlement import Settlement, point_in_poly
from waterfields import DRAIN_FT, chan_px

from .consts import GRAIN, POND_SETBACK_LIMIT, REF_HOUSEHOLDS, Poly, Pt
from .geom import crosses_poly, unit
from .plan import SitePlan

# ---- STAGE 3: where the runoff goes -------------------------------------------------------------


def drain_outfall(s: Settlement, name: str) -> Pt | None:
    """The last vertex of the field's drain collector, READ BACK from the manifest.

    Read back rather than remembered, because the manifest is what the gate reads: siting the pond
    from the same record `pond_connected_to_field` will measure against is the skill's "placement and
    its check must read the SAME manifest source" rule, one level down."""
    for ditch in s.M.get("field_ditches", []):
        if ditch.get("role") == "drain" and ditch.get("field") == name:
            pts = ditch["poly"]
            return (float(pts[-1][0]), float(pts[-1][1]))
    return None  # pragma: no cover - build_comb always emits a drain collector for a comb fan


def drain_heading(s: Settlement, name: str) -> Pt | None:
    """The direction the drain collector is running where it ends - so its continuation leaves it as
    a smooth junction rather than a hard corner."""
    for ditch in s.M.get("field_ditches", []):
        if ditch.get("role") == "drain" and ditch.get("field") == name and len(ditch["poly"]) >= 2:
            a, b = ditch["poly"][-2], ditch["poly"][-1]
            return unit(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))
    return None  # pragma: no cover - drain_outfall found the same record a line earlier


def edge_run(plan: SitePlan, frm: Pt) -> float:
    """Distance from `frm` to the canvas edge along the fall - how far a watercourse has to run to
    leave the map from here."""
    dx, dy = plan.fall
    spans = []
    if abs(dx) > 1e-6:
        spans.append(((plan.W if dx > 0 else 0.0) - frm[0]) / dx)
    if abs(dy) > 1e-6:
        spans.append(((plan.H if dy > 0 else 0.0) - frm[1]) / dy)
    return max(0.0, min(spans)) if spans else 0.0  # pragma: no cover - the fall is never the zero vector


def pond_clear_of_crop(plan: SitePlan, center: Pt, prx: float, pry: float) -> bool:
    """The two tests `pond_clear_of_field` makes, on the same envelope: no rim point inside the crop,
    no crop vertex inside the pond."""
    env = list(plan.envelope)
    rim = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
    if any(point_in_poly(center[0] + prx * ux, center[1] + pry * uy, env) for ux, uy in rim):
        return False
    return not any(((v[0] - center[0]) / prx) ** 2 + ((v[1] - center[1]) / pry) ** 2 <= 1.0 for v in env)


def pond_setback(plan: SitePlan, out: Pt, prx: float, pry: float, step: float = 14.0, limit: float = 900.0) -> float:
    """How far DOWNSLOPE of the drain outfall the pond must stand to clear the crop entirely.

    Walks outward in small steps and returns the first distance at which no rim point of the ellipse
    falls inside the field envelope and no envelope vertex falls inside the ellipse - the same two
    tests `pond_clear_of_field` makes, run against the same envelope, so the siting and the check
    cannot disagree (the skill's "adjudicate against the gate, never a re-statement of it" rule, in
    its cheap form: the predicate is copied from the check and measured on the same manifest
    geometry). A 12 px cushion past the first clear position keeps it off the line."""
    dx, dy = plan.fall
    env = list(plan.envelope)
    rim = [(math.cos(a), math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
    d = pry + 46.0  # never closer than a rim's worth below the outfall, whatever the geometry says
    while d <= limit:
        cx, cy = out[0] + dx * d, out[1] + dy * d
        clear = not any(point_in_poly(cx + prx * ux, cy + pry * uy, env) for ux, uy in rim)
        if clear:
            clear = not any(((v[0] - cx) / prx) ** 2 + ((v[1] - cy) / pry) ** 2 <= 1.0 for v in env)
        if clear:
            return d + 12.0
        d += step
    return limit  # pragma: no cover - a fan is never 900px deep past its own outfall


def stage_sink(s: Settlement, plan: SitePlan) -> None:
    """The tameike the field drains into - DERIVED from the drain, never placed by hand.

    A reservoir below the fields is sited by one fact: it must sit clear of the paddies and low
    enough that the drain reaches it downhill. So it goes a fixed set-back DOWNSLOPE of the drain's
    own outfall, wherever that outfall landed, and the drainage ditch is drawn from the outfall to
    the pond's center so the two are visibly joined. Both scale with the map: a bigger hamlet drains
    more water into a bigger pond.

    `water_sink="offmap"` draws nothing here - the drain's brook (kept in `stage_field`) already
    carries the runoff off the frame, which is what most valleys do and what the GM's brief allows."""
    name = f"{plan.spec.name.lower()}-paddies"
    out = drain_outfall(s, name)
    if out is None:  # pragma: no cover - build_comb always emits a drain collector for a comb fan
        return
    dx, dy = plan.fall
    if plan.water_sink != "pond":
        # OFF THE FRAME: the collector's brook runs on downhill and leaves the map, to join a stream
        # or another farm's drain somewhere the map does not have to care about. Its LENGTH is
        # derived per bearing below - the distance from the junction to the canvas edge along the
        # heading actually taken - because a fixed length only works on the canvas it was tuned for,
        # and a length derived for the FALL is wrong for any other bearing the search tries.
        heading = drain_heading(s, name) or (dx, dy)
        # THE ROUTE IS CHOSEN AS A WHOLE - junction and exit together.
        #
        # The brook leaves the collector at a junction point and then runs downhill off the frame.
        # The junction sits on the BISECTOR of the drain's heading and the chosen exit, so the brook
        # turns through half the angle twice rather than all of it once, and half of any angle is
        # obtuse (`water_channels_obtuse_turns`; a ditch does not fold back on itself). It TURNS WITH
        # THE BEARING for a reason learned the hard way: pinned to the fall line it was identical for
        # every candidate, so when that one leg crossed the crop all nine bearings failed alike and
        # the sweep dropped through to an untested straight line - the exact defect the sweep exists
        # to prevent, chosen deliberately.
        #
        # "Straight downhill" is right on most fans and wrong on the ones whose toe is concave, where
        # the exit clips back across the rice - so the bearing swings off the fall until the route is
        # clear, nearest first. A brook does follow the fall; the swing is small, and the alternative
        # is a watercourse drawn through a paddy.
        #
        # The junction leg is exempt from the crop test exactly when the GATE exempts it, on the same
        # test: `streams_avoid_fields` trims leading vertices that are INSIDE the field outline, so a
        # leg whose start is outside gets measured in full. Anything looser skips the one leg that
        # was crossing - a 35%-along start was tried, and the crossing was in the first 35%.
        # THE BROOK STARTS WHERE THE GATE WILL TRIM IT. `streams_avoid_fields` drops leading vertices
        # that are strictly INSIDE the field outline, which is how it exempts the anchored end - but a
        # collector whose outfall lands exactly ON the outline (within rounding) is neither in nor
        # out, so nothing is trimmed and every route from it reads as crossing the crop. There is no
        # bearing that fixes that; the start is the problem. Backing up the drain until the point is
        # genuinely inside costs nothing - the brook is the drain's own continuation, so it still
        # touches the collector at its end - and it lets the exemption do its job.
        for back_off in (0.0, 12.0, 24.0, 40.0, 60.0):
            cand = (out[0] - heading[0] * back_off, out[1] - heading[1] * back_off)
            if point_in_poly(cand[0], cand[1], plan.envelope):
                out = cand
                break
        exit_deg = math.degrees(math.atan2(dy, dx))
        anchored = point_in_poly(out[0], out[1], plan.envelope)
        best: tuple[int, Poly] | None = None
        # ...and the junction's DISTANCE from the outfall is searched too. At a fixed 70 px the
        # junction can sit inside a lobe of the fan that the collector runs past, so every bearing
        # crosses on its first leg and the best available route is still a bad one. Letting the brook
        # run a little further before it turns is what gets it clear, and it is what a brook does.
        # Ordered SWING-major and capped at +/-54 deg: `drainage_junction_smooth` wants the brook to
        # leave the collector without a kink, so a wide swing bought to clear a lobe costs more than
        # it saves. Try the nearest bearings at every junction distance before widening the angle.
        # Bearings are tried around the FALL first and then around the DRAIN'S OWN HEADING. A brook
        # continuing along the collector's line before it turns downhill is both perfectly smooth at
        # the junction (turn = 0) and already clear of the rice, since the collector is - which is the
        # combination a fan whose toe wraps a lobe cannot get any other way.
        head_deg = math.degrees(math.atan2(heading[1], heading[0]))
        for base_deg, swing, jd in ((bd, sw, j) for sw in (0, 12, -12, 24, -24, 38, -38, 54, -54) for bd in (exit_deg, head_deg) for j in (70.0, 110.0, 160.0, 230.0)):
            th = math.radians(base_deg + swing)
            bis = unit(heading[0] + math.cos(th), heading[1] + math.sin(th))
            mid = (out[0] + bis[0] * jd, out[1] + bis[1] * jd)
            # the run is measured along THIS bearing, not along the fall: a ray sized for the fall
            # and fired on another heading either stops on the map or sweeps far past it
            spans = [
                ((plan.W if math.cos(th) > 0 else 0.0) - mid[0]) / math.cos(th) if abs(math.cos(th)) > 1e-6 else 1e9,
                ((plan.H if math.sin(th) > 0 else 0.0) - mid[1]) / math.sin(th) if abs(math.sin(th)) > 1e-6 else 1e9,
            ]
            run_here = max(120.0, min(spans)) + 260.0
            end = (mid[0] + math.cos(th) * run_here, mid[1] + math.sin(th) * run_here)
            # THE JUNCTION ANGLE IS SCORED, not left to the ordering. `drainage_junction_smooth`
            # wants under 65 degrees between the drain's own heading and the brook's first leg, and
            # the crop and the angle pull against each other on a fan whose collector runs past a
            # lobe: clearing the rice wants a wide swing, the smooth junction wants a narrow one.
            # Scoring both together picks a route that satisfies both when one exists, instead of
            # ping-ponging between two rules each satisfied at the other's expense.
            turn = math.degrees(math.acos(max(-1.0, min(1.0, heading[0] * bis[0] + heading[1] * bis[1]))))
            bad = int(point_in_poly(mid[0], mid[1], plan.envelope)) + int(crosses_poly(mid, end, plan.envelope))
            bad += int(not anchored and crosses_poly(out, mid, plan.envelope))
            bad += int(turn > 55.0)
            if bad == 0:
                s.stream([out, mid, end], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8)  # s.stream reserves its own corridor
                plan.sink_brook = [out, mid, end]
                return
            if best is None or bad < best[0]:  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
                best = (bad, [out, mid, end])  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
        assert (
            best is not None
        )  # ...and if none is clean, the LEAST-BAD route, never an untested one  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
        s.stream(
            best[1], frm={"kind": "drain"}, to={"kind": "offmap"}, width=8
        )  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
        plan.sink_brook = list(best[1])  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
        return  # pragma: no cover - the least-bad brook route; no cohort fan currently blocks every bearing at every junction distance
    # Sized to the settlement: a tameike serving ~15 households reads at roughly Ikegami's 116x74 px
    # (~230 x 150 ft), and the radius scales with the square root of the households it waters, since
    # a reservoir's job is a VOLUME and its depth does not grow with the hamlet.
    grow = math.sqrt(plan.spec.households / REF_HOUSEHOLDS)
    prx, pry = 116.0 * grow, 74.0 * grow
    # THE SET-BACK IS SOLVED, NOT PICKED. `pond_clear_of_field` wants the whole ellipse outside the
    # field envelope, and the drain's outfall is not reliably outside it - a comb's envelope bows out
    # around the collector, so on some fans the outfall sits well inside the outline. Ikegami's
    # authored constant (rim + 46 px below the outfall) is true for Ikegami's fan and false for
    # others, which is exactly the failure mode the project's "derive, don't pin" rule names. So the
    # pond walks DOWNSLOPE from the outfall until its rim is genuinely clear, and stops at the first
    # position that is - the nearest legal seat, so the ditch between field and pond stays a ditch.
    back = pond_setback(plan, out, prx, pry)
    if back > POND_SETBACK_LIMIT:
        # NO ROOM FOR A RESERVOIR HERE, so the field drains off the frame instead.
        #
        # `pond_setback` walks downslope until the pond's rim clears the crop, and on a fan whose
        # toe reaches well past its own drain outfall that can be most of a canvas - at which point
        # the pond is a hard crop feature stranded in open scrub, holding the map's frame open by
        # hundreds of px for its own sake (`crop_not_held_open_by_one_feature` caught one 575 px
        # proud). A tameike is dug just below the fields it collects; one a quarter mile out is not
        # a tameike, it is a lake. Falling back to the off-map brook is the honest reading of the
        # same geometry, and the GM's brief names both sinks as equally ordinary.
        plan.water_sink = "offmap"  # pragma: no cover - the pond-to-offmap fallback; no cohort fan currently needs a tameike further than the limit
        stage_sink(s, plan)  # pragma: no cover - the pond-to-offmap fallback; no cohort fan currently needs a tameike further than the limit
        return  # pragma: no cover - the pond-to-offmap fallback; no cohort fan currently needs a tameike further than the limit
    pcx, pcy = out[0] + dx * back, out[1] + dy * back
    clamped = (max(prx + 20.0, min(plan.W - prx - 20.0, pcx)), max(pry + 20.0, min(plan.H - pry - 20.0, pcy)))
    if math.hypot(clamped[0] - pcx, clamped[1] - pcy) > 1.0 or not pond_clear_of_crop(plan, clamped, prx, pry):
        # THE CLAMP UNDOES THE SOLVE, so a clamped pond is no pond. `pond_setback` walks the tameike
        # downslope until its rim clears the crop; the clamp then pulls it back onto the canvas - and
        # straight back onto the rice it had just cleared (`pond_clear_of_field`). The reservoir has
        # nowhere to go on this map, which is the same finding as a set-back over the limit, so it
        # takes the same answer: the field drains off the frame instead.
        plan.water_sink = "offmap"
        stage_sink(s, plan)
        return
    pcx, pcy = clamped
    s.pond(pcx, pcy, prx, pry)
    plan.sink_pond = (pcx, pcy, prx, pry)
    s.M["meta"]["pond_role"] = "drainage"
    # The drainage ditch, bowed slightly off the straight line so it reads as dug earth rather than
    # a ruled connector (the gate's `channel_winds_gently` wants the same thing). Drawn in the BASE
    # water block, not the late one: the pond's fill has to paint OVER the ditch's mouth where it
    # overshoots the rim, and a late stroke composites above the fill instead
    # (`pond_fill_covers_channel_mouths`).
    bow = min(10.0, 0.08 * math.hypot(pcx - out[0], pcy - out[1]))  # a fixed 10 px bow on a SHORT run is an
    # acute hairpin (`water_channels_obtuse_turns`); proportional keeps the turn obtuse at any length
    mid = ((out[0] + pcx) / 2 - dy * bow, (out[1] + pcy) / 2 + dx * bow)
    ditch: Poly = [out, mid, (pcx, pcy)]
    # WIDTH IS THE DRAIN'S OWN, NOT A LITERAL. This is the collector's last few strides into the
    # tameike, so it carries everything the collector carries - and it used to be drawn at a flat
    # 2.5 px whatever the drain arrived at. Harmless while the net was 5-6x oversize (12.0 -> 2.5
    # reads as one line among many fat ones) and conspicuous the moment the net went to TRUE SIZE:
    # `settlement-review` measured a 5.5 px collector butting a 2.5 px stub at the pond mouth and
    # called it a pinch rather than a mouth, on the sheet's most visible water feature. Derived from
    # `DRAIN_FT[1]` so it tracks any future change to the ladder - the standing derive-don't-pin
    # rule, which a literal here quietly broke.
    outfall_w = chan_px(DRAIN_FT[1], GRAIN)
    s.field_channel(ditch, "#7C9EB0", outfall_w, outfall_w)
    # ...but the TOPOLOGY record stays at the hairline. `M["channels"]` is the connectivity graph the
    # anchor checks walk, and its widths are held in a hairline band on purpose
    # (`irrigation_channels_hairline`, `watercourses_wider_than_ditches` - a natural watercourse must
    # out-measure a field ditch by a wide margin). The DRAWN truth lives in `M["drawn_channels"]`,
    # which is where the widened stroke above is recorded. Writing the drawn width into the topology
    # record instead fires both of those checks on 14 cohort maps apiece - measured, not guessed.
    s.M["channels"].append({"poly": [[round(x, 1), round(y, 1)] for x, y in ditch], "frm": {"kind": "drain"}, "to": {"kind": "pond"}, "w": 2.5})
    # RESERVE IT AS A NO-BUILD CORRIDOR. `s.channel` and `s.stream` register one; `s.field_channel`
    # does not - which is fine for the comb's own ditches, because they run inside a field envelope
    # that is blocked ground already, and wrong for this one, which runs OUT of the field across
    # open margin where the placer is free to seat a homestead on it (`no_structure_on_channel`).
    s.corridors.append((list(ditch), 33.0))
    # A reedy fringe rims the shore - the shallow margin of any standing water.
    ring: Poly = [(pcx + (prx + 44) * math.cos(a), pcy + (pry + 44) * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
    s.marsh(ring, role="pond_fringe")
    # No building on the water.
    s.block_polys.append([(pcx - prx - 10, pcy - pry - 10), (pcx + prx + 10, pcy - pry - 10), (pcx + prx + 10, pcy + pry + 10), (pcx - prx - 10, pcy + pry + 10)])
