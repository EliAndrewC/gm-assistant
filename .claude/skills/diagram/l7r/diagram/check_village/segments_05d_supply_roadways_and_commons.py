"""Gate segments (supply roadways and commons; keys 0324_500-0602) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from .common_01_geometry import Poly, Pt, point_in_poly, seg_dist, seg_intersect, segments_cross
from .common_02_overlap_policy import in_ellipse
from .common_03_capacity import _UNBOUND, _kept

# WATERCOURSES JOIN, THEY DO NOT CROSS (GM 2026-07-24, Enokida: "many of the irrigated channels
# intersect rather than joining"). Where two irrigation strokes meet, one of them must END there -
# a T (a lateral delivering into the ring trunk) or a Y (a delivery taking off downstream) - never a
# 4-way X with a stub poking out the far side. Real wet-rice hydrology has no crossings to draw: a
# ditch either feeds another ditch or is fed by it, and where two courses genuinely had to pass at
# different levels the builders put in an aqueduct or a siphon, which is a distinct structure this
# vocabulary does not have. So any X on these maps is a drawing error.
#
# HOW A JOIN IS TOLD FROM A CROSSING: at every crossing point, take each stroke's endpoint nearest
# that point and ask whether that TIP sits inside the OTHER stroke's drawn band (perpendicular
# distance to its centerline <= its stroke half-width). If either tip is buried in the other's
# band, the meeting is a junction and the overrun is invisible under the ink. If NEITHER is, the
# stub shows and it reads as a crossing.
#
# The measure is PERPENDICULAR TO THE OTHER STROKE rather than run-length along the stub's own
# line, and that is the whole trick: a delivery ditch taking off at a shallow angle runs several px
# past the crossing yet stays under the trunk's stroke the entire way (correct, and it looks it),
# while the same overrun on a near-perpendicular T pokes straight out the far side. A run-length
# rule cannot separate those; the perpendicular one is exactly "does the stub show". Swept over
# every pool map it flagged Enokida's polder laterals (tips 2.0-2.8px outside the ring's band) and
# nothing else - Honda's, Ikegami's, Nagahara's and Hoshizora's comb offtakes overrun by a similar
# 4-8px along their own line but stay inside the canal band, and all four read as clean Y-junctions.
# The 1px slack absorbs the 0.1px coordinate rounding and the round linecap.
#
# Read from drawn_channels (the post-clip record of what was actually STROKED, widths included),
# not from field_ditches/channels: those carry pre-clip geometry, so a mouth snapped onto a pond or
# a stream would be judged at a position it is never drawn at.


# THE HEAD-RACE FORKS AND SUPPLY COMMANDS BOTH FLANKS (GM caught Inashiro's bare west margin
# 2026-08-16; researched - research/water.md "The head-race forks - supply commands both flanks").
# A gravity canal waters only ground BELOW it (Chinese canal doctrine: every tier sits on the high
# ground of ITS OWN command area; Minuma-dai 1728 divides its head into TWO canals along the two
# elevated margins with the drain down the center), and build_comb carves paddy on BOTH sides of
# the bunsuiguchi division - so a fan whose drawn supply runs down one margin only has a whole
# flank of modeled-as-watered plots with no visible water. Measured on the motivating map: ~255 ft
# of planted paddy west of Inashiro's fork against 0 ft of drawn supply. The check reads the fork
# build_comb records on the field (legacy manifests carry none, so the frozen pool skips it -
# conversion, not retrofit, is their fix per the migration doctrine) and compares each flank's
# planted cross-slope extent against the drawn main/branch reach on that flank. Thresholds are
# real feet (scaled by ftpx): a flank with more than ~150 ft of paddy needs drawn supply reaching
# at least 80 ft, or 30% of that flank's extent, whichever is greater - calibrated so a genuinely
# lopsided fan (a sliver of ground past the fork) demands nothing, while a flank the carve
# actually planted must show the arm that waters it.


def _seg_0324_500__comb_supply_commands_both_flanks(
    *,
    M: Any = _UNBOUND,
    _csf_bad: Any = _UNBOUND,
    _csf_c: Any = _UNBOUND,
    _csf_d: Any = _UNBOUND,
    _csf_deg: Any = _UNBOUND,
    _csf_ext: Any = _UNBOUND,
    _csf_f: Any = _UNBOUND,
    _csf_fork: Any = _UNBOUND,
    _csf_ftpx: Any = _UNBOUND,
    _csf_i: Any = _UNBOUND,
    _csf_reach: Any = _UNBOUND,
    _csf_ring: Any = _UNBOUND,
    _csf_s: Any = _UNBOUND,
    _csf_seen: Any = _UNBOUND,
    _csf_v: Any = _UNBOUND,
    check: Any = _UNBOUND,
    meta: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0324.500 (comb_supply_commands_both_flanks) - new check 2026-08-16, see the comment bank above."""
    _csf_bad = []
    _csf_ftpx = float(meta.get("ftpx") or 1.0)
    _csf_seen = False
    for _csf_f in M.get("fields") or []:
        _csf_fork = _csf_f.get("fork")
        _csf_deg = _csf_f.get("down_deg", meta.get("down_deg"))
        if _csf_fork is None or _csf_deg is None or _csf_f.get("kind") != "paddy":
            continue
        _csf_seen = True
        # cross-slope unit vector: fall d = (cos, sin), c = d rotated 90 deg - flank membership is
        # the SIGN of a point's cross-slope offset from the fork (an AGGREGATE bearing question is
        # fine on vertices; every quantity here is an extent, not a gap verdict)
        _csf_c = (-math.sin(math.radians(float(_csf_deg))), math.cos(math.radians(float(_csf_deg))))
        _csf_ext = [0.0, 0.0]
        for _csf_ring in _csf_f.get("plot_rings") or []:
            for _csf_v in _csf_ring:
                _csf_s = (_csf_v[0] - _csf_fork[0]) * _csf_c[0] + (_csf_v[1] - _csf_fork[1]) * _csf_c[1]
                _csf_i = 0 if _csf_s >= 0 else 1
                _csf_ext[_csf_i] = max(_csf_ext[_csf_i], abs(_csf_s))
        _csf_reach = [0.0, 0.0]
        for _csf_d in M.get("field_ditches") or []:
            if _csf_d.get("field") != _csf_f.get("name") or _csf_d.get("role") not in ("main", "branch"):
                continue
            for _csf_v in _csf_d["poly"]:
                _csf_s = (_csf_v[0] - _csf_fork[0]) * _csf_c[0] + (_csf_v[1] - _csf_fork[1]) * _csf_c[1]
                _csf_i = 0 if _csf_s >= 0 else 1
                _csf_reach[_csf_i] = max(_csf_reach[_csf_i], abs(_csf_s))
        for _csf_i in (0, 1):
            if _csf_ext[_csf_i] > 150.0 / _csf_ftpx and _csf_reach[_csf_i] < max(80.0 / _csf_ftpx, 0.3 * _csf_ext[_csf_i]):
                _csf_bad.append(
                    f"{_csf_f.get('name')}: the {'+cross' if _csf_i == 0 else '-cross'} flank has ~{round(_csf_ext[_csf_i] * _csf_ftpx)} ft "
                    f"of paddy but its drawn supply reaches only ~{round(_csf_reach[_csf_i] * _csf_ftpx)} ft from the fork"
                )
    if _csf_seen:
        check(
            "comb_supply_commands_both_flanks",
            not _csf_bad,
            "a gravity canal commands only the ground BELOW it, so a comb fan planted on both sides of its "
            "bunsuiguchi fork must DRAW supply down both margins - canal A along one, canal B partway down the "
            "other, tapering (the Minuma-dai split; research/water.md 'The head-race forks - supply commands "
            f"both flanks'). Give the fan a canal-B offtake (hamletgen OFFTAKE_LADDER offtakes_b) so the second "
            f"arm is inked: {_csf_bad}",
        )
    return _kept(
        locals(),
        (
            '_csf_bad',
            '_csf_c',
            '_csf_d',
            '_csf_deg',
            '_csf_ext',
            '_csf_f',
            '_csf_fork',
            '_csf_ftpx',
            '_csf_i',
            '_csf_reach',
            '_csf_ring',
            '_csf_s',
            '_csf_seen',
            '_csf_v',
        ),
    )


def _seg_0325___wj_strokes(*, M: Any = _UNBOUND, c: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 325 (_wj_strokes, c) - body verbatim from the legacy gate() (feature 022)."""
    _wj_strokes = [c for c in M.get("drawn_channels", []) or [] if len(c.get("pts") or []) >= 2]
    return _kept(locals(), ('_wj_strokes', 'c'))


def _seg_0326__water_channels_join_not_cross(
    *,
    _wj_band: Any = _UNBOUND,
    _wj_bbox: Any = _UNBOUND,
    _wj_boxes: Any = _UNBOUND,
    _wj_cross: Any = _UNBOUND,
    _wj_strokes: Any = _UNBOUND,
    _wj_stub: Any = _UNBOUND,
    _wj_tip_outside: Any = _UNBOUND,
    _wj_worst: Any = _UNBOUND,
    at: Any = _UNBOUND,
    ax0: Any = _UNBOUND,
    ax1: Any = _UNBOUND,
    ay0: Any = _UNBOUND,
    ay1: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e: Any = _UNBOUND,
    ha: Any = _UNBOUND,
    hb: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ia: Any = _UNBOUND,
    ib: Any = _UNBOUND,
    j: Any = _UNBOUND,
    other: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pa: Any = _UNBOUND,
    pb: Any = _UNBOUND,
    pts: Any = _UNBOUND,
    tip: Any = _UNBOUND,
    xs: Any = _UNBOUND,
    ys: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 326 (water_channels_join_not_cross) - body verbatim from the legacy gate() (feature 022)."""
    if _wj_strokes:

        def _wj_band(c: Any) -> float:
            return max(float(c.get("w0", 3.0)), float(c.get("w1", 3.0))) / 2

        def _wj_bbox(pts: Poly) -> tuple[float, float, float, float]:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return min(xs), min(ys), max(xs), max(ys)

        def _wj_tip_outside(pts: Poly, other: Poly, other_half: float, at: Pt) -> float:
            """How far the end of `pts` NEAREST the crossing sits OUTSIDE `other`'s drawn band."""
            tip = min((pts[0], pts[-1]), key=lambda e: math.hypot(e[0] - at[0], e[1] - at[1]))
            return min(seg_dist(tip[0], tip[1], other[i], other[i + 1]) for i in range(len(other) - 1)) - other_half

        _wj_boxes = [_wj_bbox(c["pts"]) for c in _wj_strokes]
        _wj_cross: list[tuple[int, int]] = []  # type: ignore[no-redef]
        for ia in range(len(_wj_strokes)):
            for ib in range(ia + 1, len(_wj_strokes)):
                ax0, ay0, ax1, ay1 = _wj_boxes[ia]
                bx0, by0, bx1, by1 = _wj_boxes[ib]
                if ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0:
                    continue
                pa, pb = _wj_strokes[ia]["pts"], _wj_strokes[ib]["pts"]
                ha, hb = _wj_band(_wj_strokes[ia]), _wj_band(_wj_strokes[ib])
                _wj_worst: tuple[float, Pt] | None = None  # type: ignore[no-redef]
                for i in range(len(pa) - 1):
                    for j in range(len(pb) - 1):
                        if not segments_cross(pa[i], pa[i + 1], pb[j], pb[j + 1]):
                            continue
                        at = seg_intersect(pa[i], pa[i + 1], pb[j], pb[j + 1])
                        if at is None:
                            continue  # pragma: no cover - segments_cross already excludes the parallel case
                        _wj_stub = min(_wj_tip_outside(pa, pb, hb, at), _wj_tip_outside(pb, pa, ha, at))
                        if _wj_worst is None or _wj_stub > _wj_worst[0]:
                            _wj_worst = (_wj_stub, at)
                if _wj_worst is not None and _wj_worst[0] > 1.0:
                    _wj_cross.append((round(_wj_worst[1][0]), round(_wj_worst[1][1])))
        check(
            "water_channels_join_not_cross",
            not _wj_cross,
            f"irrigation channel(s) CROSSING rather than joining at {sorted(set(_wj_cross))[:5]} - where two "
            f"watercourses meet, one must END at the junction (a T feeding the trunk, or a Y taking off from it); "
            f"neither tip lands inside the other's drawn band here, so a stub pokes out the far side and the pair "
            f"reads as a 4-way intersection. Snap the joining stroke's tip onto the other's drawn centerline",
        )
    return _kept(
        locals(),
        (
            '_wj_band',
            '_wj_bbox',
            '_wj_boxes',
            '_wj_cross',
            '_wj_stub',
            '_wj_tip_outside',
            '_wj_worst',
            'at',
            'ax0',
            'ax1',
            'ay0',
            'ay1',
            'bx0',
            'bx1',
            'by0',
            'by1',
            'c',
            'ha',
            'hb',
            'i',
            'ia',
            'ib',
            'j',
            'pa',
            'pb',
        ),
    )


# no farm field overlaps a road OR a town street (the roadbed/street band must not clip
# a field) - the road leading into town must not run through a farm field
# EVERY DRAWN WAY, not just the road and the streets (GM 2026-08-12: "Inashiro has village paths
# overlapping with rice paddies... I also think there's supposed to be a rule that paths don't
# pass through marshland"). Both rules below were written for roads and duly never saw a village
# LANE or an alley - the same shape as `ring_road_kept_clear`'s hand-written key list, and it
# looks exactly like a passing check. A lane is a narrower way, not a different KIND of thing:
# its tread is trodden earth that a farmer walks in the dry, so it belongs on the baulk between
# plots and on dry ground, never in the standing water of a paddy or across a reed marsh.


def _seg_0327__roadways() -> dict[str, Any]:
    """Gate segment 327 (roadways) - body verbatim from the legacy gate() (feature 022)."""
    roadways = []  # type: ignore[var-annotated]
    return _kept(locals(), ('roadways',))


def _seg_0328__roadways_1(*, M: Any = _UNBOUND, road: Any = _UNBOUND, roadways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 328 (roadways) - body verbatim from the legacy gate() (feature 022)."""
    if road:
        roadways.append((road, M.get("road_width", 26) / 2 + 2))
    return _kept(locals(), ('roadways',))


def _seg_0329__roadways_2(*, M: Any = _UNBOUND, roadways: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 329 (roadways, st) - body verbatim from the legacy gate() (feature 022)."""
    roadways += [(st["pts"], st["w"] / 2 + 2) for st in M.get("town_streets", [])]
    return _kept(locals(), ('roadways', 'st'))


def _seg_0330__ln(*, M: Any = _UNBOUND, ln: Any = _UNBOUND, roadways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 330 (ln, roadways) - body verbatim from the legacy gate() (feature 022)."""
    roadways += [(ln["pts"], ln.get("w", 5) / 2 + 2) for ln in M.get("lanes", [])]
    return _kept(locals(), ('ln', 'roadways'))


def _seg_0331__al(*, M: Any = _UNBOUND, al: Any = _UNBOUND, roadways: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 331 (al, roadways) - body verbatim from the legacy gate() (feature 022)."""
    roadways += [(al["pts"], al.get("w", 10) / 2 + 2) for al in M.get("alleys", [])]
    return _kept(locals(), ('al', 'roadways'))


def _seg_0332__fields_clear_of_road(
    *,
    M: Any = _UNBOUND,
    _b: Any = _UNBOUND,
    _drawn: Any = _UNBOUND,
    bad_fr: Any = _UNBOUND,
    check: Any = _UNBOUND,
    e: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fcr_a: Any = _UNBOUND,
    fcr_b: Any = _UNBOUND,
    fcr_hit: Any = _UNBOUND,
    fcr_k: Any = _UNBOUND,
    fcr_k2: Any = _UNBOUND,
    fcr_n: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    k: Any = _UNBOUND,
    m: Any = _UNBOUND,
    mpoly: Any = _UNBOUND,
    nmp: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    roadways: Any = _UNBOUND,
    rx: Any = _UNBOUND,
    ry: Any = _UNBOUND,
    t: Any = _UNBOUND,
    vx0: Any = _UNBOUND,
    vx1: Any = _UNBOUND,
    vy0: Any = _UNBOUND,
    vy1: Any = _UNBOUND,
    wet_road: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 332 (fields_clear_of_road, roads_clear_of_marsh) - body verbatim from the legacy gate() (feature 022)."""
    if roadways:
        # MEASURED AGAINST THE DRAWN CROP, not the whole envelope (settlement-review, 2026-08-12).
        # A field's `outline` is not all rice: a comb fan's envelope carries a tail past the last
        # plot that exists only to block house placement, and Ueda's gen says so in as many words.
        # Testing the raw outline therefore reported a lane "in the paddy" where the render shows
        # bare parchment with ten farmhouses standing on it - and the cure for that phantom broke a
        # village spine in two, stranded 25 homesteads, and collapsed a shrine's seven-arch sando to
        # one when the re-pack moved it. `vis_bbox` is the bbox of the drawn plot vertices and every
        # field records it, so both sides can read the same thing: a way is only in the rice where
        # it is inside the outline AND inside the drawn extent. The GM sees ink, not envelopes.
        bad_fr = []
        for f in fields:
            ol = f["outline"]
            n = len(ol)
            vx0, vy0, vx1, vy1 = f.get("vis_bbox") or f.get("bbox") or (-1e9, -1e9, 1e9, 1e9)

            def _drawn(px: float, py: float, _ol: Any = ol, _b: Any = (vx0, vy0, vx1, vy1)) -> bool:
                return _b[0] <= px <= _b[2] and _b[1] <= py <= _b[3] and point_in_poly(px, py, _ol)

            for poly, hw in roadways:
                # local names are suffixed: `gate()` is one enormous scope and `a`/`b`/`k`/`i` are
                # all bound to other things in it (this skill's CLAUDE.md warns about exactly this).
                fcr_hit = False
                for fcr_k in range(len(poly) - 1):
                    fcr_a, fcr_b = poly[fcr_k], poly[fcr_k + 1]
                    fcr_n = max(2, int(math.hypot(fcr_b[0] - fcr_a[0], fcr_b[1] - fcr_a[1]) / 6.0))
                    if any(_drawn(fcr_a[0] + (fcr_b[0] - fcr_a[0]) * t / fcr_n, fcr_a[1] + (fcr_b[1] - fcr_a[1]) * t / fcr_n) for t in range(fcr_n + 1)):
                        fcr_hit = True
                        break
                if not fcr_hit:  # ...and the way's own tread may not reach a DRAWN plot edge either
                    fcr_hit = any(_drawn(px, py) and seg_dist(px, py, poly[fcr_k2], poly[fcr_k2 + 1]) < hw for px, py in ol for fcr_k2 in range(len(poly) - 1))
                if fcr_hit:
                    bad_fr.append(f["name"])
                    break
        check(
            "fields_clear_of_road",
            not bad_fr,
            f"field(s) run under a way: {sorted(set(bad_fr))} - a road, street, lane or alley is trodden ground and a "
            f"paddy is standing water; a farm track runs on the BAULK between plots or round the field's margin, never through it",
        )

        # ROADS STAY CLEAR OF MARSHLAND (GM, Hoshizora 2026-07: the tameike's reed fringe ran under
        # the Imperial Road). A roadbed is engineered dry ground; none of these maps draw a causeway,
        # so a road/street entering a marsh patch is a placement error, not a feature.
        wet_road = []
        for m in M.get("marshes", []):
            if m.get("role") == "defense":
                continue  # an approach road THROUGH the defensive wet belt is a CAUSEWAY (the renderer keeps the tread bare via the corridor skip) - few, constricted approaches are the belt's military purpose, not a placement error
            mpoly = m.get("poly") or []
            nmp = len(mpoly)
            if nmp < 3:
                continue
            for poly, hw in roadways:
                if (
                    any(seg_dist(px, py, poly[k], poly[k + 1]) < hw for px, py in mpoly for k in range(len(poly) - 1))
                    or any(point_in_poly(rx, ry, mpoly) for rx, ry in poly)
                    or any(segments_cross(poly[k], poly[k + 1], mpoly[e], mpoly[(e + 1) % nmp]) for k in range(len(poly) - 1) for e in range(nmp))
                ):
                    wet_road.append((round(m["x"]), round(m["y"])))
                    break
        check(
            "roads_clear_of_marsh",
            not wet_road,
            f"a way runs through marshland at {sorted(set(wet_road))[:4]} - a roadbed is engineered dry ground and a "
            f"village lane is trodden earth; neither survives a reed marsh without a causeway, and none of these maps "
            f"draws one. Route the way round the wet ground, or put the marsh where the way is not",
        )
    return _kept(
        locals(),
        (
            '_drawn',
            'bad_fr',
            'e',
            'f',
            'fcr_a',
            'fcr_b',
            'fcr_hit',
            'fcr_k',
            'fcr_k2',
            'fcr_n',
            'hw',
            'k',
            'm',
            'mpoly',
            'n',
            'nmp',
            'ol',
            'poly',
            'px',
            'py',
            'rx',
            'ry',
            't',
            'vx0',
            'vx1',
            'vy0',
            'vy1',
            'wet_road',
        ),
    )


# THE POND STAYS CLEAR OF THE RICE PADDIES (GM, Hoshizora 2026-07). A pond is a distinct water
# body BESIDE the crop - a reservoir above the field or a drainage tameike below it - joined by a
# channel, never overlapping the planted paddy itself.


def _seg_0333__pond_clear_of_paddies(
    *,
    a: Any = _UNBOUND,
    check: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    i: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    pcx_: Any = _UNBOUND,
    pcy_: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    prx_: Any = _UNBOUND,
    pry_: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    rim_pts: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
    wet_paddy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 333 (pond_clear_of_paddies) - body verbatim from the legacy gate() (feature 022)."""
    if pond and fields:
        pcx_, pcy_, prx_, pry_ = pond
        rim_pts = [(pcx_ + prx_ * math.cos(a), pcy_ + pry_ * math.sin(a)) for a in [i * math.pi / 12 for i in range(24)]]
        wet_paddy = []
        for f in fields:
            if f.get("kind") != "paddy":
                continue
            ol = f["outline"]
            if any(in_ellipse(vx, vy, pond) for vx, vy in ol) or any(point_in_poly(px, py, ol) for px, py in rim_pts) or point_in_poly(pcx_, pcy_, ol):
                wet_paddy.append(f["name"])
        check(
            "pond_clear_of_paddies",
            not wet_paddy,
            f"the pond overlaps rice paddy field(s) {sorted(set(wet_paddy))} - a pond sits BESIDE the crop (a reservoir above it or a tameike below it), joined by a channel, never over the planted paddy",
        )
    return _kept(locals(), ('a', 'f', 'i', 'ol', 'pcx_', 'pcy_', 'prx_', 'pry_', 'px', 'py', 'rim_pts', 'vx', 'vy', 'wet_paddy'))


def _seg_0597__woodland_commons_within_the_frame(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 597 (woodland_commons_within_the_frame) - hand-added 2026-08-16 past the
    legacy range (see _seg_0595 for the numbering convention). New-style: writes=()."""
    # A WOODLAND PARCEL THE CROP CUTS OFF IS DRAWN BUT NOT SHOWN (known-open ledger
    # 2026-08-16, Sawada: two of three parcels wholly above the frame, the third
    # half-cropped under the title placard; Kashikawa and Mizuguchi the same shape). The
    # commons deliberately do NOT set the frame (crop_to_content: scrub and woods bleed at
    # the edge), so a parcel seated past the kept window vanishes without any check
    # noticing - the invisible-feature class, same family as the blind extractor keys. The
    # scan now confines woodland to the predicted kept window (open_ground_patches); this
    # holds it there. 70% of the parcel's bbox must be inside the view: a parcel CLIPPING
    # at the edge reads as "more wood that way" and is fine; one mostly outside is not on
    # the map in any honest sense. Bbox area is exact for the scan's axis-aligned squares
    # and a fair proxy for any other parcel shape.
    if M["meta"].get("generated_by") and M["meta"].get("view"):
        _wf_x0, _wf_y0, _wf_vw, _wf_vh = (float(_v) for _v in M["meta"]["view"])
        _wf_x1, _wf_y1 = _wf_x0 + _wf_vw, _wf_y0 + _wf_vh
        _wf_bad: list[tuple[int, int, int]] = []
        for _wf_c in M.get("commons", []):
            if _wf_c.get("role") != "woodland" or not _wf_c.get("poly"):
                continue
            _wf_bx0 = min(float(p[0]) for p in _wf_c["poly"])
            _wf_bx1 = max(float(p[0]) for p in _wf_c["poly"])
            _wf_by0 = min(float(p[1]) for p in _wf_c["poly"])
            _wf_by1 = max(float(p[1]) for p in _wf_c["poly"])
            _wf_area = max(1e-9, (_wf_bx1 - _wf_bx0) * (_wf_by1 - _wf_by0))
            _wf_inter = max(0.0, min(_wf_bx1, _wf_x1) - max(_wf_bx0, _wf_x0)) * max(0.0, min(_wf_by1, _wf_y1) - max(_wf_by0, _wf_y0))
            _wf_frac = _wf_inter / _wf_area
            if _wf_frac < 0.7:
                _wf_bad.append((round((_wf_bx0 + _wf_bx1) / 2), round((_wf_by0 + _wf_by1) / 2), round(100 * _wf_frac)))
        check(
            "woodland_commons_within_the_frame",
            not _wf_bad,
            f"{len(_wf_bad)} woodland commons parcel(s) mostly or wholly outside the kept view (center, %-inside): {_wf_bad[:4]} - a coppice the crop cuts off is drawn but not shown, and the commons never set the frame, so nothing else notices; seat woodland inside the predicted kept window (open_ground_patches confines the scan)",
        )
    return _kept(locals(), ())


def _seg_0599__woodland_commons_on_dry_ground(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 599 (woodland_commons_on_dry_ground) - hand-added 2026-08-16 past the
    legacy range (see _seg_0595 in segments_08 for the numbering convention). New-style:
    writes=()."""
    # A COPPICE DOES NOT STAND IN THE MARSH (settlement-review x3, 2026-08-16: confining the
    # woodland scan to the kept frame pushed parcels onto the wet toe - Inashiro seated one
    # 100% inside the marsh polygon with ZERO crowns of ink, Sawada one at 97%, Mizuguchi one
    # at ~60%). The engine's own crown filter refuses wet ground, so a wet-seated parcel
    # renders as a few stray crowns or nothing at all: a record claiming a woodland the
    # drawing does not deliver - and the crowns are ink-only, so no crown count can catch it;
    # the SEAT vs the recorded marsh poly is the manifest-visible truth. (A real wet-margin
    # willow/alder coppice exists historically, but this engine draws no wet-tolerant stand -
    # honesty of record-vs-ink is the rule being held.) 30% wet is the line: a marsh-fringe
    # parcel may lap the haze a little; one mostly wet cannot read as itself. Grid-sampled
    # 5x5 over the parcel bbox against every recorded marsh poly.
    if M["meta"].get("generated_by"):
        _wd_marshes = [[(float(v[0]), float(v[1])) for v in _wd_m.get("poly") or []] for _wd_m in M.get("marshes", [])]
        _wd_marshes = [_wd_m for _wd_m in _wd_marshes if len(_wd_m) >= 3]
        _wd_bad: list[tuple[int, int, int]] = []
        if _wd_marshes:
            for _wd_c in M.get("commons", []):
                if _wd_c.get("role") != "woodland" or not _wd_c.get("poly"):
                    continue
                _wd_bx0 = min(float(p[0]) for p in _wd_c["poly"])
                _wd_bx1 = max(float(p[0]) for p in _wd_c["poly"])
                _wd_by0 = min(float(p[1]) for p in _wd_c["poly"])
                _wd_by1 = max(float(p[1]) for p in _wd_c["poly"])
                _wd_wet = 0
                for _wd_i in range(5):
                    for _wd_j in range(5):
                        _wd_x = _wd_bx0 + (_wd_bx1 - _wd_bx0) * (_wd_i + 0.5) / 5
                        _wd_y = _wd_by0 + (_wd_by1 - _wd_by0) * (_wd_j + 0.5) / 5
                        if any(point_in_poly(_wd_x, _wd_y, _wd_m) for _wd_m in _wd_marshes):
                            _wd_wet += 1
                if _wd_wet > 0.3 * 25:
                    _wd_bad.append((round((_wd_bx0 + _wd_bx1) / 2), round((_wd_by0 + _wd_by1) / 2), round(100 * _wd_wet / 25)))
        check(
            "woodland_commons_on_dry_ground",
            not _wd_bad,
            f"{len(_wd_bad)} woodland commons parcel(s) mostly on the marsh (center, %-wet): {_wd_bad[:4]} - the crown filter refuses wet ground, so a wet-seated parcel renders as a few stray crowns claiming a whole woodland; seat the coppice on dry ground (open_ground_patches treats marsh polys as keep-outs)",
        )
    return _kept(locals(), ())


def _seg_0602__woodland_commons_visibly_stocked(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 602 (woodland_commons_visibly_stocked) - hand-added 2026-08-16 past the
    legacy range (see _seg_0595 in segments_08 for the numbering convention). New-style:
    writes=()."""
    # A CLAIMED WOODLAND MUST CARRY A CANOPY THE MANIFEST CAN COUNT (known-open ledger
    # 2026-08-16, both review rounds independently): the stand crowns used to be SVG ink only,
    # so a parcel whose crowns were all culled by keep-outs shipped as a claimed woodland with
    # nothing drawn and no check able to see it (Inashiro's 100%-marsh parcel drew ZERO crowns
    # behind a green gate). `commons(role="woodland")` now records each drawn crown into
    # `tree_crowns` and the count onto the parcel; this holds the declaration-exists invariant:
    # a parcel with no `crowns` key predates the recording (regenerate), and one under 5 crowns
    # is a claimed woodland the drawing does not deliver (re-seat it - the marsh/frame keep-outs
    # and the shrink ladder are the levers).
    if M["meta"].get("generated_by"):
        _ws_bad: list[tuple[int, int, Any]] = []
        for _ws_c in M.get("commons", []):
            if _ws_c.get("role") != "woodland":
                continue
            _ws_n = _ws_c.get("crowns")
            if _ws_n is None or int(_ws_n) < 5:
                _ws_bad.append((round(float(_ws_c.get("x", 0))), round(float(_ws_c.get("y", 0))), _ws_n))
        check(
            "woodland_commons_visibly_stocked",
            not _ws_bad,
            f"{len(_ws_bad)} woodland commons parcel(s) with no recorded canopy (center, crowns; None = unrecorded): {_ws_bad[:4]} - a parcel claiming a woodland must draw one and record its crowns (commons role=woodland now writes tree_crowns + a per-parcel count); under 5 crowns the stand does not read as a wood, so re-seat the parcel on more open dry ground",
        )
    return _kept(locals(), ())
