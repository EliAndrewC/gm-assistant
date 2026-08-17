"""Gate segments (homesteads) - bodies verbatim from check_village.py (feature 024 package split; registry order preserved)."""

import math
from typing import Any

from l7r.diagram.settlement import label_aabb, label_quad, paddy_wet_rings, ring_touches, sat_overlap, surface_water_dist

from .common_01_geometry import (
    _LABEL_BY_KIND,
    _LABEL_GROUP,
    _LABEL_GROUPS,
    _OVERLAP_STRUCTS,
    _box_hits_poly,
    _struct_rect,
    kiln_quarters,
    point_in_poly,
    poly_area,
    pt_to_rect,
    rect_corners,
    seg_dist,
    segments_cross,
    within_edge_gap,
)
from .common_02_overlap_policy import edge_dist, in_ellipse, torii_halfbox
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _kept

# a VILLAGE / HAMLET map clothes its margins in a CONTINUOUS RING of dry marginal land (settlements.md
# 'Village windbreak' back-slope doctrine, the GM's rule: every "empty" edge of the frame is the satoyama
# toposequence - grazing scrub, coppice, marsh, dry plots - never open plain). Proving ring TOPOLOGY is
# hard; gate the SYMPTOM instead: the fraction of the framed view covered by NO ground feature at all.
# Why 12%: calibrated over the whole pool (2026-07-20) - hamlets sit at 0% bare, the ring-conforming
# villages at 0-8.4% (Hoshigaoka the max; its tan shows only as thin seams between feathered scatter
# bands), while the motivating defect (Ueda, whose ring bands were drawn for the full canvas and then
# mostly CROPPED OUT of the tightened frame) sat at 28% - so 12% cleanly separates "seams between
# scatters" from "open plain". Town/city sheets are urban (streets/wards/walls, which these feature sets
# do not model) and outside the doctrine's scope. Sampled on a 25-px grid; polygon features count via
# point-in-poly, box features (structures, the pond) via their bounds.


def _seg_0268__margins_form_continuous_ring(
    *,
    EX0: Any = _UNBOUND,
    EX1: Any = _UNBOUND,
    EY0: Any = _UNBOUND,
    EY1: Any = _UNBOUND,
    M: Any = _UNBOUND,
    _bare: Any = _UNBOUND,
    _total: Any = _UNBOUND,
    bare_frac: Any = _UNBOUND,
    bb: Any = _UNBOUND,
    bx0: Any = _UNBOUND,
    bx1: Any = _UNBOUND,
    by0: Any = _UNBOUND,
    by1: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cover_bbs: Any = _UNBOUND,
    cover_boxes: Any = _UNBOUND,
    cover_polys: Any = _UNBOUND,
    f: Any = _UNBOUND,
    fields: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    k: Any = _UNBOUND,
    o: Any = _UNBOUND,
    p: Any = _UNBOUND,
    pcx: Any = _UNBOUND,
    pcy: Any = _UNBOUND,
    prx: Any = _UNBOUND,
    pry: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 268 (margins_form_continuous_ring) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("village", "hamlet"):
        cover_polys = [f["outline"] for f in fields]
        for k in ("commons", "marshes", "village_groves", "groves", "dry_plots", "gardens", "threshing_yards"):
            cover_polys += [o["poly"] for o in M.get(k, []) if o.get("poly") and len(o["poly"]) >= 3]
        cover_boxes = []
        for k in ("houses", "buildings", "manors", "religious", "shrines", "farm_sheds", "storehouses", "cemeteries", "gardens", "threshing_yards"):
            for o in M.get(k, []):
                if "x" in o and "w" in o and "h" in o:
                    cover_boxes.append((o["x"] - o["w"] / 2, o["y"] - o["h"] / 2, o["x"] + o["w"] / 2, o["y"] + o["h"] / 2))
        if M.get("pond"):
            pcx, pcy, prx, pry = M["pond"]
            cover_boxes.append((pcx - prx, pcy - pry, pcx + prx, pcy + pry))
        cover_bbs = [(min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)) for p in cover_polys]
        _bare = _total = 0
        gy = EY0 + 12.5
        while gy < EY1:
            gx = EX0 + 12.5
            while gx < EX1:
                _total += 1
                if not (
                    any(bx0 <= gx <= bx1 and by0 <= gy <= by1 for bx0, by0, bx1, by1 in cover_boxes)
                    or any(bb[0] <= gx <= bb[2] and bb[1] <= gy <= bb[3] and point_in_poly(gx, gy, p) for p, bb in zip(cover_polys, cover_bbs, strict=True))
                ):
                    _bare += 1
                gx += 25
            gy += 25
        bare_frac = _bare / _total if _total else 1.0
        check(
            "margins_form_continuous_ring",
            bare_frac <= 0.12,
            f"{bare_frac:.0%} of the framed map is bare open ground (over the 12% seam allowance) - every empty margin is dry marginal land and must be clothed in the satoyama ring (grazing scrub / coppice / marsh / dry plots, broad edge-spanning bands), and the bands must lie INSIDE the cropped view, not off-frame",
        )
    return _kept(
        locals(),
        ('_', '_bare', '_total', 'bare_frac', 'bb', 'bx0', 'bx1', 'by0', 'by1', 'cover_bbs', 'cover_boxes', 'cover_polys', 'f', 'gx', 'gy', 'k', 'o', 'p', 'pcx', 'pcy', 'prx', 'pry', 'x', 'y'),
    )


# SWEPT GROUND stays swept: a sacred/funerary feature keeps a tended clearing - the shrine's keidai, the
# torii's sando collar, the graveyard's trimmed grave collar (settlements.md 'Swept ground around sacred +
# funerary features') - and the loose ground-cover scatter (commons scrub, marsh reeds) skips it. But the
# scatter can only skip clearings that EXIST when it runs: a cemetery/shrine placed AFTER a commons/marsh
# draw registers its collar too late, and the scrub has already dotted the swept ground (this bit Ueda's
# graveyard, 2026-07-20: the new S grazing band drew at stage 3b, the cemetery registered its collar at
# stage 4d, and tufts landed among the grave markers). The engine records each cover draw's ordinal (`seq`
# on commons/marsh entries) and each clearing's ordinal at registration (`seq` = covers already drawn), so
# ORDER is checkable from the manifest: a cover that overlaps a clearing and drew at seq <= the clearing's
# seq predates it - violation. Fix in the gen: s.reserve_clearing(...) BEFORE the scatter (or reorder).


def _seg_0269__late() -> dict[str, Any]:
    """Gate segment 269 (late) - body verbatim from the legacy gate() (feature 022)."""
    late = []  # type: ignore[var-annotated]
    return _kept(locals(), ('late',))


def _seg_0270___clearings(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 270 (_clearings) - body verbatim from the legacy gate() (feature 022)."""
    _clearings = M.get("clearings", [])
    return _kept(locals(), ('_clearings',))


def _seg_0271___clr_bbs() -> dict[str, Any]:
    """Gate segment 271 (_clr_bbs) - body verbatim from the legacy gate() (feature 022)."""
    _clr_bbs = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_clr_bbs',))


def _seg_0272___clr_bbs_1(*, _clearings: Any = _UNBOUND, _clr_bbs: Any = _UNBOUND, cl: Any = _UNBOUND, cxs: Any = _UNBOUND, cys: Any = _UNBOUND, p: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 272 (_clr_bbs, cl, cxs, cys) - body verbatim from the legacy gate() (feature 022)."""
    for cl in _clearings:
        cxs = [p[0] for p in cl["poly"]]
        cys = [p[1] for p in cl["poly"]]
        _clr_bbs.append((min(cxs), min(cys), max(cxs), max(cys)))
    return _kept(locals(), ('_clr_bbs', 'cl', 'cxs', 'cys', 'p'))


def _seg_0273__cbb(
    *,
    M: Any = _UNBOUND,
    _clearings: Any = _UNBOUND,
    _clr_bbs: Any = _UNBOUND,
    cbb: Any = _UNBOUND,
    cl: Any = _UNBOUND,
    cov: Any = _UNBOUND,
    exposed: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gp: Any = _UNBOUND,
    guards: Any = _UNBOUND,
    late: Any = _UNBOUND,
    sx: Any = _UNBOUND,
    sy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 273 (cbb, cl, cov, exposed) - body verbatim from the legacy gate() (feature 022)."""
    for cl, cbb in zip(_clearings, _clr_bbs, strict=True):
        for cov in list(M.get("commons", [])) + list(M.get("marshes", [])):
            if cov.get("seq") is None or cov["seq"] > cl["seq"] or not cov.get("poly") or not _box_hits_poly(cbb, cov["poly"]):
                continue
            # the scatter predates this clearing where they overlap - but the SAME ground may have been
            # RESERVED in time: a clearing registered before the cover drew (guard.seq < cov.seq) already
            # made the scatter skip it (s.reserve_clearing first, then the feature registers its own
            # duplicate collar late - the documented, harmless pattern). Sample the clearing's bbox: a point
            # is EXPOSED only if it lies in the clearing AND the cover's poly and in no pre-cover guard
            # clearing. Guards test the exact POLY, not the bbox - clearings are organic blobs (GM
            # 2026-07-23), and a bbox guard would over-credit a lobed outline with ground it never swept.
            guards = [g["poly"] for g in _clearings if g["seq"] < cov["seq"]]
            exposed = False
            sy = cbb[1] + 4.0
            while not exposed and sy < cbb[3]:
                sx = cbb[0] + 4.0
                while not exposed and sx < cbb[2]:
                    if point_in_poly(sx, sy, cl["poly"]) and point_in_poly(sx, sy, cov["poly"]) and not any(point_in_poly(sx, sy, gp) for gp in guards):
                        exposed = True
                    sx += 8
                sy += 8
            if exposed:
                late.append((cov.get("role", "?"), round(cbb[0]), round(cbb[1])))
    return _kept(locals(), ('cbb', 'cl', 'cov', 'exposed', 'g', 'gp', 'guards', 'late', 'sx', 'sy'))


def _seg_0274__scatter_respects_swept_clearings(*, check: Any = _UNBOUND, late: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 274 (scatter_respects_swept_clearings) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "scatter_respects_swept_clearings",
        not late,
        f"ground-cover scatter drawn BEFORE the swept clearing it overlaps (cover role, clearing at): {late[:3]} - the scrub/reed scatter only skips clearings that exist when it runs, so the shrine/torii/graveyard collar got dotted over; s.reserve_clearing(...) the ground BEFORE the commons/marsh draw (or place the feature first)",
    )
    return _kept(locals(), ())


# A LABEL must not sit on a building/structure it does NOT name (town + city scale, where features
# carry distinct identities). A label may overlap the feature(s) it names - its own building/compound,
# or (for a zone label) any building of that cluster - and may clip a street-fronting shop or an
# interleaved servant house (those line every quarter, so never a victim). But where a label spills
# onto a DIFFERENT-identity feature it tells the reader that feature is something it is not (a
# "Monastery" label over the graveyard, a "graveyard" label over the monastery). Each labeled feature
# carries a GROUP; the label text declares which group(s) it may cover - else it fires.


def _seg_0275__labels_clear_of_other_buildings(
    *,
    FUNERARY: Any = _UNBOUND,
    L: Any = _UNBOUND,
    LABEL_FREE: Any = _UNBOUND,
    M: Any = _UNBOUND,
    _bb: Any = _UNBOUND,
    _grp: Any = _UNBOUND,
    _label_allows: Any = _UNBOUND,
    _lg: Any = _UNBOUND,
    _lk: Any = _UNBOUND,
    _lq: Any = _UNBOUND,
    _lrecs: Any = _UNBOUND,
    _tv: Any = _UNBOUND,
    _tzd: Any = _UNBOUND,
    _tzh: Any = _UNBOUND,
    _tzu: Any = _UNBOUND,
    _vr: Any = _UNBOUND,
    a: Any = _UNBOUND,
    allow: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    dx: Any = _UNBOUND,
    dy: Any = _UNBOUND,
    g: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    it: Any = _UNBOUND,
    k_: Any = _UNBOUND,
    kind: Any = _UNBOUND,
    mislabel: Any = _UNBOUND,
    r_: Any = _UNBOUND,
    sa: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
    txt: Any = _UNBOUND,
    vics: Any = _UNBOUND,
    w: Any = _UNBOUND,
    x0: Any = _UNBOUND,
    x1: Any = _UNBOUND,
    xs: Any = _UNBOUND,
    y0: Any = _UNBOUND,
    y1: Any = _UNBOUND,
    ys: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 275 (labels_clear_of_other_buildings) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city"):
        LABEL_FREE = {"shop", "servant"}
        FUNERARY = {"cemetery", "mausoleum", "cremation", "ossuary"}

        def _grp(kind: str) -> str:
            if kind in ("samurai", "samurai_large"):
                return "samurai"
            if kind in ("merchant", "merchant_house", "merchant_large"):
                return "merchant"
            if kind == "laborer_large":
                return "laborer"
            return kind

        def _bb(it: dict[str, Any]) -> tuple[float, float, float, float]:
            rot = it.get("rot", 0)
            hw, hh = it.get("w", 0) / 2, it.get("h", 0) / 2
            if not rot:
                return it["x"] - hw, it["y"] - hh, it["x"] + hw, it["y"] + hh
            a = math.radians(rot)
            ca, sa = math.cos(a), math.sin(a)
            xs = [it["x"] + dx * ca - dy * sa for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
            ys = [it["y"] + dx * sa + dy * ca for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
            return min(xs), min(ys), max(xs), max(ys)

        # EVERY solid feature is a caption victim, read from the _LABEL_GROUP registry rather than a
        # hand-written key list (GM 2026-07-26). The list this replaced had fallen behind twice: the
        # martial hall and the dojo had to be remembered into it, and the execution-ground feature's
        # three keys were never in it at all, so a foreign caption over an execution ground shipped
        # green. Anything deliberately NOT a victim is named in _LABEL_EXEMPT with its reason, and
        # every_solid_feature_classified_for_labels fires if a new key is in neither.
        vics = [(_grp(b.get("kind", "")), _bb(b)) for k_ in _LABEL_BY_KIND for b in M.get(k_, []) if _grp(b.get("kind", "")) not in LABEL_FREE]
        for _lk, _lg in _LABEL_GROUP.items():
            _lrecs = M.get(_lk)
            if isinstance(_lrecs, dict):  # governor_mansion is a singleton, not a list
                _lrecs = [_lrecs]
            for r_ in _lrecs or []:
                if not isinstance(r_, dict):
                    continue  # pragma: no cover - defensive: every classified key stores dicts
                if "w" in r_:
                    vics.append((_lg, _bb(r_)))
                elif r_.get("vr"):
                    # a WELLHEAD has no w/h - its drawn extent is the marker radius `vr` (SKILL.md's
                    # location-marker doctrine). Without this branch, adding "wells" to _LABEL_GROUP
                    # would classify it and still check nothing, because the builder filtered on "w".
                    _vr = float(r_["vr"])
                    vics.append((_lg, (r_["x"] - _vr, r_["y"] - _vr, r_["x"] + _vr, r_["y"] + _vr)))
        # A TORII is recorded as a bare [x, y, z] triple, not a dict, so the loop above skipped it even
        # once it was classified - the same trap the wellhead's `vr` branch documents, one shape further
        # out. Its drawn extent is the true-scale glyph box (torii_halfbox), which settlement._torii and
        # the frame checks read too.
        _tzh, _tzu, _tzd = torii_halfbox(float(M.get("meta", {}).get("ftpx", 1) or 1))
        for _tv in M.get("torii", []):
            vics.append((_LABEL_GROUP["torii"], (_tv[0] - _tzh, _tv[1] - _tzu, _tv[0] + _tzh, _tv[1] + _tzd)))

        def _label_allows(txt: str) -> set[str]:
            t = txt.lower()
            if "guard" in t or "inspection" in t:  # "guard house" / "guard station" / "front gate (...)"
                return {"gate"}
            if "flophouse" in t:
                return {"flophouse"}
            if "ministry" in t:
                return {"ministry"}
            if "granar" in t:  # "domain granaries" / "Imperial granaries": the plural does not CONTAIN the group word "granary", so the derived rule alone cannot permit it
                return {"granary"}
            if "governor" in t or "mansion" in t:
                return {"governor"}
            if "manor" in t or "magistra" in t:  # magistrate AND magistracy - the institution naming (GM 2026-08-09)
                return {"estate"}
            if any(w in t for w in ("temple", "shrine", "monastery", "chapel")):
                return {"temple"}
            if any(w in t for w in ("graveyard", "burial", "cemetery", "cremation", "mausoleum", "ossuary")):
                return FUNERARY  # type: ignore[no-any-return]  # the funerary structures cluster, so a funerary label may cover any of them
            if "samurai" in t:
                return {"samurai", "estate"}
            if "laborer" in t or "laborer" in t:
                return {"laborer"}
            if "burakumin" in t or "agricultur" in t:  # the in-wall farming district houses burakumin AND works its farms
                return {"burakumin", "farmhouse"}
            if "barn" in t:
                return {"barn"}
            if "merchant" in t:
                return {"merchant"}
            if any(w in t for w in ("street", "avenue", "road")):
                return {"merchant"}  # a street/road label runs along its frontage, so it may clip the storefronts it lines
            if "drum/bell" in t or t.strip() == "tower":  # the two-line zhonggulou caption (GM 2026-07-24)
                return {"drum tower"}
            if "theater stage" in t:
                # A theater stage is TEMPLE FURNITURE - `theater_stage`'s own docstring sites it in a
                # temple/monastery precinct, and `theater_stage_by_temple` enforces that. So its
                # caption is inside a precinct wherever it sits, and the halls are the only things
                # near enough to caption it against. Same shape as "samurai" -> {"samurai", "estate"}:
                # the label may cover the enclosure its subject belongs to, not just its own glyph.
                return {"temple"}
            # A CAPTION MAY ALWAYS COVER THE THING IT NAMES, derived rather than hand-listed: the
            # _LABEL_GROUP registry's group names ARE the caption words ("brewery", "martial hall",
            # "execution ground"), so a new feature earns this permission by being classified, with
            # no second list to remember. The branches above stay because they are SYNONYMS - a
            # caption says "Temple of Benten" or "Governor's Mansion", not "temple" or "governor".
            named = {g for g in _LABEL_GROUPS if g in t}
            return named  # empty for farmland / market / theater stage / title labels, which name no building

        mislabel = []
        for L in M.get("labels", []):
            if len(L) <= 5:
                continue
            allow = _label_allows(L[5])
            _lq = label_quad(L) if len(L) > 7 else None  # a TILTED caption is judged by its true drawn quad, not the pre-tilt box
            for g, (x0, y0, x1, y1) in vics:
                if g in allow:
                    continue
                if sat_overlap(_lq, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]) if _lq else (L[0] < x1 and x0 < L[2] and L[1] < y1 and y0 < L[3]):
                    mislabel.append(f"{L[5]!r} over a {g}")
                    break
        check(
            "labels_clear_of_other_buildings",
            not mislabel,
            f"label(s) sitting on a feature they do not name (a label may cover only the thing it labels, or a fronting shop/servant house): {sorted(set(mislabel))}",
        )
    return _kept(
        locals(),
        (
            'FUNERARY',
            'L',
            'LABEL_FREE',
            '_bb',
            '_grp',
            '_label_allows',
            '_lg',
            '_lk',
            '_lq',
            '_lrecs',
            '_tv',
            '_tzd',
            '_tzh',
            '_tzu',
            '_vr',
            'allow',
            'b',
            'g',
            'k_',
            'mislabel',
            'r_',
            'vics',
            'x0',
            'x1',
            'y0',
            'y1',
        ),
    )


# LABELS must stay WITHIN the rendered image. Plenty of things rightly run off the edge - farm
# fields, roads, samurai country estates, farmhouses, the countryside continuing beyond the frame -
# but a label that spills past the edge is clipped and unreadable, so every label's bounding box
# must sit inside the frame. The frame is the cropped view (a city map crops tight to the walls,
# so its EX/EY bounds are the viewBox) or, uncropped, the full canvas. The title is placed directly
# (not recorded in M["labels"]) and sits inside the frame by construction.


def _seg_0276__L_1(*, EX0: Any = _UNBOUND, EX1: Any = _UNBOUND, EY0: Any = _UNBOUND, EY1: Any = _UNBOUND, L: Any = _UNBOUND, _la: Any = _UNBOUND, labels: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 276 (L, _la, off_img) - body verbatim from the legacy gate() (feature 022)."""
    off_img = [L[5] if len(L) > 5 else "label" for L in labels for _la in (label_aabb(L),) if _la[0] < EX0 - 1 or _la[1] < EY0 - 1 or _la[2] > EX1 + 1 or _la[3] > EY1 + 1]
    return _kept(locals(), ('L', '_la', 'off_img'))


def _seg_0277__labels_within_image(*, check: Any = _UNBOUND, off_img: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 277 (labels_within_image) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "labels_within_image",
        not off_img,
        f"label(s) running off the edge of the image - a label must sit fully within the frame (fields/roads/estates/farmhouses may run off, labels may not): {sorted(set(off_img))}",
    )
    return _kept(locals(), ())


# every WELL must sit AMONG the buildings it serves (ANY scale): a communal well is the draw-point for
# the households around it, so one out in open countryside with no building beside it is unreal. (A city's
# pack fills in around its wells; the rural tiers place wells only near houses via place_wells(..., near=...),
# since their grid would otherwise scatter into the fields.) A well may also serve a RELIGIOUS building - a
# set-apart shrine's own ablution well stands beside the shrine, not among houses - so religious halls count.


def _seg_0278__all_wells(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 278 (all_wells) - body verbatim from the legacy gate() (feature 022)."""
    all_wells = M.get("wells", [])
    return _kept(locals(), ('all_wells',))


def _seg_0279__wells_among_dwellings(
    *,
    M: Any = _UNBOUND,
    _k: Any = _UNBOUND,
    _q: Any = _UNBOUND,
    all_wells: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    ddims: Any = _UNBOUND,
    dwell_all: Any = _UNBOUND,
    in_paddy: Any = _UNBOUND,
    mean_dia: Any = _UNBOUND,
    med: Any = _UNBOUND,
    ring: Any = _UNBOUND,
    stray: Any = _UNBOUND,
    vr_w: Any = _UNBOUND,
    wet_rings: Any = _UNBOUND,
    wl: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 279 (wells_among_dwellings, wells_clear_of_paddies, wells_sized_to_buildings) - body verbatim from the legacy gate() (feature 022)."""
    if all_wells:
        dwell_all = M.get("buildings", []) + M.get("houses", []) + M.get("religious", [])
        # A KILN WORKS' cottages are dwellings, and its well stands among THEM (GM 2026-07-27).
        # They are recorded inside the works' own record rather than in M["houses"] - see s.kiln
        # for why - so a check that reads only the settlement's housing stock would call the works'
        # own well stray. Read them here rather than exempting private wells: the rule's teeth are
        # for a well out in open country, and this one is genuinely among the houses it serves.
        dwell_all = dwell_all + [_q for _k in M.get("kilns", []) for _q in kiln_quarters(_k)]
        stray = [
            (round(wl["x"]), round(wl["y"])) for wl in all_wells if dwell_all and not any(within_edge_gap(wl, b, 95) for b in dwell_all)
        ]  # the TRUE gap to the served building's edge (fair to a large hall); the half-diagonal this used
        # to subtract over-stated a big hall's extent by up to 41% - see edge_gap (GM audit, 2026-07-27)
        check(
            "wells_among_dwellings",
            not stray,
            f"well(s) standing in open ground with no building within ~95px - a well serves the households around it and must sit AMONG them, not out in the fields/countryside: {stray[:4]}",
        )

        # AND NOT IN A RICE PADDY (GM 2026-07-27: "wells on dry crops are okay, but not in rice
        # paddies, surely"). A paddy is a puddled, bunded basin held under standing water through the
        # growing season: a wellhead drawn in one is standing in the water it is supposed to be an
        # alternative to, and a shaft sunk there takes the field's own surface water. Dry crops are
        # a different matter and stay allowed - a hatake plot is worked ground you can walk on.
        #
        # THE GAP THIS CLOSES, which was wider than it looked. `_well_ground_clear` already refused a
        # stream, channel, ditch, canal, pond and DRY plot, its docstring saying "you do not dig one
        # in the middle of a crop plot" - the wet plots, where it matters most, were simply never
        # added. Nor could the overlap matrix catch it: `fields` is classed PADDY_RECONSTRUCTED, i.e.
        # permissive, because a plot's polygon is not stored and its rebuilt extent is too
        # approximate to accuse anything with. So this is one of the "precise paddy checks" that
        # class defers to. It reads `paddy_wet_rings` - the DRAWN basins where a field records them,
        # the outline where it does not - which is the same water the SITER reads, so the two cannot
        # disagree; that helper carries the why of both halves. Note what the drawn-basin reading
        # deliberately still ALLOWS: the fan's unplanted rim slack, inside the smoothed envelope but
        # clear of every basin, which is legitimate margin ground and is where a boxed-in steading's
        # well goes. Strictness matches the dry-plot rule exactly - the DRAWN head may not lap water.
        wet_rings = paddy_wet_rings(M)
        if wet_rings:
            in_paddy = []
            for wl in all_wells:
                vr_w = float(wl.get("vr") or wl.get("r") or 8.0)
                if any(ring_touches(wl["x"], wl["y"], vr_w, ring) for ring in wet_rings):
                    in_paddy.append((round(wl["x"]), round(wl["y"])))
            check(
                "wells_clear_of_paddies",
                not in_paddy,
                f"wellhead(s) at {in_paddy[:4]} standing in a rice paddy - a paddy is flooded and bunded, so a well cannot be sunk in one (a DRY plot is different and is allowed, and so is the fan's unplanted rim slack); move the head onto the dooryard/margin ground it serves",
            )

        # THE WELL IS A LOCATION MARKER under the stroke convention (GM ruling 2026-07-21): a real
        # curb is ~3-4 ft (sub-glyph at every scale), so the wellhead marks the well's TO-SCALE
        # LOCATION with a legible marker whose own pixels are not claimed to be to scale - the same
        # doctrine as the linework floor, and deliberately NOT a violation of everything-is-to-scale.
        # The marker must be DRAWN at a size proportional to the buildings: it scales with the map
        # grain (bscale) the way the houses do, so it reads as a consistent ~half-a-dwelling at every
        # tier. A fixed pixel size looks right in the dense city but shrinks to a speck beside a
        # village/town's larger houses. Each well records its drawn radius `vr`; the mean well
        # diameter should be a sensible fraction of the median dwelling.
        ddims = [max(b["w"], b["h"]) for b in dwell_all if "w" in b and "h" in b]
        if ddims and any("vr" in wl for wl in all_wells):
            med = sorted(ddims)[len(ddims) // 2]
            mean_dia = 2 * sum(wl.get("vr", 5) for wl in all_wells) / len(all_wells)
            check(
                "wells_sized_to_buildings",
                0.35 <= mean_dia / med <= 0.85,
                f"wells are mis-sized for this map - drawn at {mean_dia:.0f}px against a ~{med:.0f}px median dwelling "
                f"({mean_dia / med:.0%}; want ~40-80%): a wellhead must scale with the map grain (bscale), not a fixed pixel size",
            )
    return _kept(locals(), ('_k', '_q', 'b', 'ddims', 'dwell_all', 'in_paddy', 'mean_dia', 'med', 'ring', 'stray', 'vr_w', 'wet_rings', 'wl'))


# LANES stay OFF the dry crop plots (GM 2026-07-21, caught on Hikari no Sato: the west field-spur
# ran straight through two barley plots). A trodden path does not cross row crops - historically a
# path runs on the baulk/margin BETWEEN plots, and the engine already keeps the reverse direction
# honest (dry plots are no-build ground for houses, groves skip them). A lane may TOUCH a plot's
# edge (paths hug field margins by design), so only points >3px INSIDE a plot fire.


def _seg_0280___lane_on_crop() -> dict[str, Any]:
    """Gate segment 280 (_lane_on_crop) - body verbatim from the legacy gate() (feature 022)."""
    _lane_on_crop = []  # type: ignore[var-annotated]
    return _kept(locals(), ('_lane_on_crop',))


def _seg_0281___dps(*, M: Any = _UNBOUND, dp: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 281 (_dps, dp) - body verbatim from the legacy gate() (feature 022)."""
    _dps = [dp["poly"] for dp in M.get("dry_plots", [])]
    return _kept(locals(), ('_dps', 'dp'))


def _seg_0282___ax_1(
    *,
    M: Any = _UNBOUND,
    _ax: Any = _UNBOUND,
    _ay: Any = _UNBOUND,
    _bx: Any = _UNBOUND,
    _by: Any = _UNBOUND,
    _dp: Any = _UNBOUND,
    _dps: Any = _UNBOUND,
    _i: Any = _UNBOUND,
    _k: Any = _UNBOUND,
    _lane_on_crop: Any = _UNBOUND,
    _ln: Any = _UNBOUND,
    _n: Any = _UNBOUND,
    _pts: Any = _UNBOUND,
    _px: Any = _UNBOUND,
    _py: Any = _UNBOUND,
    _t: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 282 (_ax, _ay, _bx, _by) - body verbatim from the legacy gate() (feature 022)."""
    if _dps:
        for _ln in M.get("lanes", []):
            _pts = _ln["pts"]
            for _i in range(len(_pts) - 1):
                (_ax, _ay), (_bx, _by) = _pts[_i], _pts[_i + 1]
                _n = max(2, int(math.hypot(_bx - _ax, _by - _ay) / 8))
                for _t in range(_n + 1):
                    _px, _py = _ax + (_bx - _ax) * _t / _n, _ay + (_by - _ay) * _t / _n
                    # depth INSIDE the plot = distance to its boundary (poly_dist is 0 for interior points)
                    if any(point_in_poly(_px, _py, _dp) and min(seg_dist(_px, _py, _dp[_k], _dp[(_k + 1) % len(_dp)]) for _k in range(len(_dp))) > 3 for _dp in _dps):
                        _lane_on_crop.append((round(_px), round(_py)))
                        break
                else:
                    continue
                break
    return _kept(locals(), ('_ax', '_ay', '_bx', '_by', '_dp', '_i', '_k', '_lane_on_crop', '_ln', '_n', '_pts', '_px', '_py', '_t'))


def _seg_0283__lanes_clear_of_dry_plots(*, _lane_on_crop: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 283 (lanes_clear_of_dry_plots) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "lanes_clear_of_dry_plots",
        not _lane_on_crop,
        f"lane(s) run THROUGH a dry crop plot at {_lane_on_crop[:3]} - a trodden path crosses no row crops; route it on the baulk between plots or around the hem (a lane may touch a plot edge, not its interior)",
    )
    return _kept(locals(), ())


# WELLS SIZED TO THE POPULATION (GM 2026-07-21) - a DELIBERATE LIBERTY, banded. What the research found
# (see settlements.md 'Wells - research + deliberate liberty' for the full note): historically a south-China
# rice village of ~70 households ran 1-3 communal drinking wells TOTAL - surface water (canal/pond, settled
# and boiled) covered most drinking, wells were expensive subscription-financed capital, the classical
# jingtian "8 families per well" was an ideal nobody practiced, and one open well physically serves ~400
# people (Sphere/UNICEF anchors; a nucleated village is ~250m across, so carrying distance never binds).
# The dense ~10-18 households/well pattern is URBAN tenement (nagaya) density; per-farmstead wells are the
# shallow-water-table plain pattern. THE LIBERTY: Rokugan is deliberately unusually well-run, and generous
# wells express that - villages run ~1 communal well per 8-26 households (vs the historical 1-3 total),
# hamlets down to per-farmstead (2-20 hh/well; the dispersed-farm shallow-table pattern made honest).
# Shrine (temizu) ablution wells are tagged shrine=True by the engine and excluded from the count.


def _seg_0284__wells_sized_to_population(
    *,
    M: Any = _UNBOUND,
    _draw_wells: Any = _UNBOUND,
    _whh: Any = _UNBOUND,
    _whi: Any = _UNBOUND,
    _wlo: Any = _UNBOUND,
    _wr: Any = _UNBOUND,
    check: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    w: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 284 (wells_sized_to_population) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("village", "hamlet") and meta.get("households"):
        _draw_wells = [w for w in M.get("wells", []) if not w.get("shrine")]
        _whh = meta["households"]
        _wlo, _whi = (2.0, 20.0) if scale == "hamlet" else (8.0, 26.0)
        _wr = _whh / len(_draw_wells) if _draw_wells else float("inf")
        check(
            "wells_sized_to_population",
            _wlo <= _wr <= _whi,
            f"{len(_draw_wells)} communal well(s) for {_whh} households = {_wr:.1f} hh/well, outside the {scale} band [{_wlo:.0f}-{_whi:.0f}] - Rokugan's prosperity liberty runs generous wells (settlements.md 'Wells'); shrine temizu wells are excluded from the count",
        )
    return _kept(locals(), ('_draw_wells', '_whh', '_whi', '_wlo', '_wr', 'w'))


# WATER ACCESS for the rural tiers (town/village/hamlet): every settlement needs communal WELLS, and
# every household must be able to reach water. Wells dot the dwellings (one per ~20-25 households),
# but a farm household may instead draw from the irrigation network it sits beside - a channel, the
# pond, the stream, the moat - so a dwelling counts as watered if a WELL OR an irrigation watercourse
# is within reach. (The CITY tier has its own finer well suite - density, block-interior placement,
# the samurai-quarter exemption - so this covers the village/hamlet/town tiers the same way.)


def _seg_0285_000__wells(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.000 (wells) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet'):
        wells = M.get("wells", [])
    return _kept(locals(), ('wells',))


def _seg_0285_001__b(*, M: Any = _UNBOUND, b: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.001 (b, dwell) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet'):
        dwell = M.get("houses", []) + [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS]
    return _kept(locals(), ('b', 'dwell'))


# A WELL stands BESIDE a shrine, never ON its hall or UNDER its torii arch (a wellhead drawn on the hall
# or in the gateway reads wrong). remote_shrine_has_own_well WANTS a well close by - but beside it, clear
# of the footprints. Circle (well disc) vs rect (hall / the torii arch's x +/-19, y -10..+18 box). Root
# cause when it fires: wells were scattered BEFORE the shrine/torii were placed, so their block-outs did
# not yet exist - place the shrine_hall (with its torii) BEFORE place_wells / shrine_well.


def _seg_0285_002__r(*, M: Any = _UNBOUND, r: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.002 (r, sacred) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet'):
        sacred = [(r["x"], r["y"], r["w"] / 2, r["h"] / 2) for r in M.get("religious", [])]
    return _kept(locals(), ('r', 'sacred'))


def _seg_0285_003__sacred(*, M: Any = _UNBOUND, sacred: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.003 (sacred, t) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet'):
        sacred += [(t[0], t[1] + 4, 19, 14) for t in M.get("torii", [])]
    return _kept(locals(), ('sacred', 't'))


def _seg_0285_004__wells_clear_of_shrine_and_torii(
    *,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    check: Any = _UNBOUND,
    ddx: Any = _UNBOUND,
    ddy: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    on_sacred: Any = _UNBOUND,
    sacred: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    wells: Any = _UNBOUND,
    wl: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.004 (wells_clear_of_shrine_and_torii) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and wells and sacred:
        on_sacred = []
        for wl in wells:
            for bx, by, hw, hh in sacred:
                ddx = wl["x"] - bx - max(-hw, min(hw, wl["x"] - bx))
                ddy = wl["y"] - by - max(-hh, min(hh, wl["y"] - by))
                if ddx * ddx + ddy * ddy < wl["r"] * wl["r"]:
                    on_sacred.append((round(wl["x"]), round(wl["y"])))
                    break
        check(
            "wells_clear_of_shrine_and_torii",
            not on_sacred,
            f"{len(on_sacred)} well(s) overlap a shrine hall or torii arch at {on_sacred[:4]} - a wellhead "
            f"stands BESIDE the shrine, never on the hall or under the gateway; place the shrine + torii "
            f"BEFORE the wells so they are blocked out",
        )
    return _kept(locals(), ('bx', 'by', 'ddx', 'ddy', 'hh', 'hw', 'on_sacred', 'wl'))


def _seg_0285_005__wells_clear_of_trees(
    *,
    M: Any = _UNBOUND,
    _clumps: Any = _UNBOUND,
    _cr_max: Any = _UNBOUND,
    _forest: Any = _UNBOUND,
    _grects: Any = _UNBOUND,
    _wl_polys: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cr: Any = _UNBOUND,
    crown_grid: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gh: Any = _UNBOUND,
    gw: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    on_trees: Any = _UNBOUND,
    p: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tr: Any = _UNBOUND,
    tx: Any = _UNBOUND,
    ty: Any = _UNBOUND,
    vr: Any = _UNBOUND,
    wells: Any = _UNBOUND,
    wl: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.005 (wells_clear_of_trees) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and wells:
        # a WELLHEAD is a clean draw-point: no tree canopy may reach it (a well lost under the wood reads
        # wrong). Gather every tree feature - the communal fengshui GROVE clumps (windbreak/water-mouth/copse,
        # each a center + drawn radius), the per-house YASHIKIRIN grove rects, a big FOREST, and the managed-
        # WOODLAND coppice patches - and fire on any well whose drawn head (vr) overlaps one. Fix at placement:
        # the grove is placed AFTER the wells and skips them (with a keep-out wide enough for the canopy).
        _clumps = [(cx, cy, g.get("r", 6)) for g in M.get("village_groves", []) for cx, cy in g.get("clumps", [])]
        _grects = [(g["x"], g["y"], g["w"], g["h"]) for g in M.get("groves", [])]
        _forest = M.get("forest")
        _wl_polys = [c["poly"] for c in M.get("commons", []) if c.get("role") == "woodland"]
        on_trees = []
        for wl in wells:
            wx, wy, vr = wl["x"], wl["y"], wl.get("vr", wl.get("r", 8))
            if (
                any(math.hypot(wx - cx, wy - cy) < vr + cr for cx, cy, cr in _clumps)
                or any(abs(wx - gx) < gw / 2 + vr and abs(wy - gy) < gh / 2 + vr for gx, gy, gw, gh in _grects)
                or (_forest and point_in_poly(wx, wy, _forest))
                or any(point_in_poly(wx, wy, p) for p in _wl_polys)
                # ... and no DRAWN crown may reach the head either (the reserved-area tests above are
                # coarse: a grove's recorded rect/clump is where its trees MAY stand, tree_crowns is
                # where they actually DO). See structures_clear_of_trees for the same rule on roofs.
                or any(math.hypot(wx - tx, wy - ty) < vr + tr for tx, ty, tr in crown_grid.near_rect(wx - vr - _cr_max, wy - vr - _cr_max, wx + vr + _cr_max, wy + vr + _cr_max))
            ):
                on_trees.append((round(wx), round(wy)))
        check(
            "wells_clear_of_trees",
            not on_trees,
            f"well(s) {on_trees[:4]} sit UNDER trees - a wellhead is a clean draw-point, not lost in the wood; "
            f"keep it clear of the fengshui grove, the per-house groves, the forest, and the coppice patches "
            f"(place the wells BEFORE the grove so it skips them, with a well keep-out wide enough for the canopy)",
        )
    return _kept(locals(), ('_clumps', '_forest', '_grects', '_wl_polys', 'c', 'cr', 'cx', 'cy', 'g', 'gh', 'gw', 'gx', 'gy', 'on_trees', 'p', 'tr', 'tx', 'ty', 'vr', 'wl', 'wx', 'wy'))


def _seg_0285_006__settlement_has_wells(
    *,
    M: Any = _UNBOUND,
    REACH: Any = _UNBOUND,
    SHRINE_FAR: Any = _UNBOUND,
    SHRINE_WELL_GAP: Any = _UNBOUND,
    b: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dry: Any = _UNBOUND,
    dwell: Any = _UNBOUND,
    h: Any = _UNBOUND,
    i: Any = _UNBOUND,
    lines: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    pond: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    shrine_hill: Any = _UNBOUND,
    st: Any = _UNBOUND,
    wellless: Any = _UNBOUND,
    wells: Any = _UNBOUND,
    wl: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.006 (remote_shrine_has_own_well, settlement_dwellings_watered, settlement_has_wells) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and dwell:
        check(
            "settlement_has_wells",
            len(wells) >= max(1, round(len(dwell) / 25)),
            f"a {scale} of {len(dwell)} households has only {len(wells)} communal well(s) - every settlement "
            f"keeps wells (about one per 20-25 households); scatter them among the dwellings with s.place_wells(...)",
        )
        lines = [c["poly"] for c in M.get("channels", [])] + [st["poly"] for st in M.get("streams", [])] + ([M["moat"]] if M.get("moat") else [])
        pond = M.get("pond")
        REACH = round(760 / float(meta.get("ftpx") or meta.get("ft_per_px") or 2.0))  # ~760 ft, in px at this map's scale (380 at 2 ft/px)
        dry = []
        for h in dwell:
            # the surface-water half is the SHARED predicate `settlement.surface_water_dist` -
            # the same call hamletgen.place_wells makes when deciding which houses need a well
            # (known-open ledger 2026-08-16: two definitions of "needs a well" had drifted).
            # `lines`/`pond` above stay bound for downstream-segment parity; the verdict reads
            # the helper.
            d = min((math.hypot(h["x"] - wl["x"], h["y"] - wl["y"]) for wl in wells), default=1e9)
            d = min(d, surface_water_dist(M, h["x"], h["y"]))
            if d > REACH:
                dry.append((round(h["x"]), round(h["y"])))
        check(
            "settlement_dwellings_watered",
            not dry,
            f"{len(dry)} household(s) more than {REACH}px from any water source - a well, or an irrigation channel / pond / stream / moat: {dry[:4]} - put a well within reach",
        )

        # A shrine/temple set sufficiently APART from the village keeps its OWN WELL close by for purification
        # (temizu): too far to walk to the village's shared wells, it needs a dedicated draw-point right beside
        # it - and specifically a WELL, not just any water (a ditch/pond is not an ablution source). A shrine
        # AMONG or near the houses shares the village wells (exempt). "Set apart" = the nearest dwelling is more
        # than SHRINE_FAR px away; "close by" = a well within SHRINE_WELL_NEAR px.
        SHRINE_FAR, SHRINE_WELL_GAP = 150, 70
        shrine_hill = M.get("hill")
        wellless = []
        for r in M.get("religious", []):
            if shrine_hill and in_ellipse(r["x"], r["y"], shrine_hill):
                continue  # a hilltop/mountain shrine draws from a spring/basin, not a dug well
            if min((math.hypot(r["x"] - b["x"], r["y"] - b["y"]) for b in dwell), default=1e9) <= SHRINE_FAR:
                continue  # among/near the houses -> shares the village wells
            if not any(within_edge_gap(r, wl, SHRINE_WELL_GAP) for wl in wells):  # the TRUE gap to the hall's edge (a big monastery's well sits further out)
                wellless.append((round(r["x"]), round(r["y"])))
        check(
            "remote_shrine_has_own_well",
            not wellless,
            f"{len(wellless)} shrine/temple(s) set apart from the village (>{SHRINE_FAR}px from any house) with no well beside them - a remote shrine keeps its own well for ablution: {wellless[:4]}",
        )
    return _kept(locals(), ('REACH', 'SHRINE_FAR', 'SHRINE_WELL_GAP', 'b', 'c', 'd', 'dry', 'h', 'i', 'lines', 'ln', 'pond', 'r', 'shrine_hill', 'st', 'wellless', 'wl'))


def _seg_0285_007__fdef(*, fdef: Any = _UNBOUND, fields: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.007 (fdef, fields_ol) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        fields_ol = [fdef["outline"] for fdef in fields]
    return _kept(locals(), ('fdef', 'fields_ol'))


def _seg_0285_008__yards(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.008 (yards) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        yards = M.get("threshing_yards", [])
    return _kept(locals(), ('yards',))


# the HEADMAN is NOT exempt (GM 2026-07-21, caught on Hikari no Sato): the old role=="headman"
# carve-out here existed only because the dispersed-style headman() predated the homestead
# bundle and drew a lone house - the check was written around the bug. The headman is the
# LARGEST farmstead in the village and threshes its own rice like every other household.


def _seg_0285_009__h(*, h: Any = _UNBOUND, houses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.009 (h, occ_h) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        occ_h = [h for h in houses if h.get("kind") != "abandoned"]
    return _kept(locals(), ('h', 'occ_h'))


# the work yard (niwa) was UNIVERSAL: EVERY farmhouse threshed and dried its own rice on its own
# yard, so EVERY farmhouse must have one (a firm 100%). The generator guarantees this by making
# the yard integral to farmstead placement - a house is only sited where its yard also fits
# (nudging it as needed) - so a farmhouse without a yard is a generator bug, not a density limit.


def _seg_0285_010__h_1(*, h: Any = _UNBOUND, occ_h: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, yards: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.010 (h, t, without) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        without = [(round(h["x"]), round(h["y"])) for h in occ_h if not any(t["of"][0] == h["x"] and t["of"][1] == h["y"] for t in yards)]
    return _kept(locals(), ('h', 't', 'without'))


def _seg_0285_011__harvest_yards_present(*, check: Any = _UNBOUND, occ_h: Any = _UNBOUND, scale: Any = _UNBOUND, without: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.011 (harvest_yards_present) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "harvest_yards_present",
            not without,
            f"a {scale} threshes and dries its rice at the farmstead, and the work yard was universal: "
            f"{len(without)} of {len(occ_h)} farmhouses have NO threshing/drying yard {without[:3]} - every "
            f"farmhouse must have one (placement makes the yard integral to the farmstead)",
        )
    return _kept(locals(), ())


# the yard is the farmstead's own dry work apron, SMALLER than the house it serves (not a
# second dwelling). Each yard records `of` = its parent farmhouse center.


def _seg_0285_012__h_2(*, h: Any = _UNBOUND, houses: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.012 (h, hmap) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        hmap = {(round(h["x"]), round(h["y"])): h["w"] * h["h"] for h in houses}
    return _kept(locals(), ('h', 'hmap'))


def _seg_0285_013__oversize(*, hmap: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, yards: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.013 (oversize, t) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        oversize = [(round(t["x"]), round(t["y"])) for t in yards if t["w"] * t["h"] >= hmap.get((round(t["of"][0]), round(t["of"][1])), 0)]
    return _kept(locals(), ('oversize', 't'))


def _seg_0285_014__harvest_yards_smaller_than_farmhouse(*, check: Any = _UNBOUND, oversize: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.014 (harvest_yards_smaller_than_farmhouse) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("harvest_yards_smaller_than_farmhouse", not oversize, f"threshing yard(s) are not smaller than their farmhouse: {oversize[:3]} - the niwa is a small dry apron beside the house")
    return _kept(locals(), ())


# the yard is the maeniwa - the SOUTH-facing front work yard. Rice must dry in the SUN and
# minka face south, so the yard sits on the house's south/front side (or, if the paddy blocks
# that, a side), but NEVER the shady NORTH back. +y is south here, so a yard must not sit
# meaningfully north of (above) its own farmhouse center (`of[1]`).


def _seg_0285_015__shady(*, scale: Any = _UNBOUND, t: Any = _UNBOUND, yards: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.015 (shady, t) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        shady = [(round(t["x"]), round(t["y"])) for t in yards if t["y"] < t["of"][1] - 5]
    return _kept(locals(), ('shady', 't'))


def _seg_0285_016__harvest_yards_on_sunny_side(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, shady: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.016 (harvest_yards_on_sunny_side) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "harvest_yards_on_sunny_side",
            not shady,
            f"threshing yard(s) sit on the shady NORTH/back side of their farmhouse: {shady[:3]} - the niwa is the "
            f"south-facing front work yard (rice must dry in the sun), so it belongs on the house's south/front side",
        )
    return _kept(locals(), ())


# the yard is a DRY tamped floor: its whole footprint must stay out of the flooded paddies.


def _seg_0285_017__in_paddy(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.017 (in_paddy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        in_paddy = []  # type: ignore[var-annotated]
    return _kept(locals(), ('in_paddy',))


def _seg_0285_018__e(
    *,
    e: Any = _UNBOUND,
    fc: Any = _UNBOUND,
    fields_ol: Any = _UNBOUND,
    in_paddy: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    t: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
    yards: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.018 (e, fc, in_paddy, k) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for t in yards:
            fc = rect_corners(_struct_rect(t))
            if any(
                any(point_in_poly(px, py, ol) for px, py in fc)
                or any(point_in_poly(vx, vy, fc) for vx, vy in ol)
                or any(segments_cross(fc[e], fc[(e + 1) % 4], ol[k], ol[(k + 1) % len(ol)]) for e in range(4) for k in range(len(ol)))
                for ol in fields_ol
            ):
                in_paddy.append((round(t["x"]), round(t["y"])))
    return _kept(locals(), ('e', 'fc', 'in_paddy', 'k', 'ol', 'px', 'py', 't', 'vx', 'vy'))


def _seg_0285_019__harvest_yards_clear_of_paddies(*, check: Any = _UNBOUND, in_paddy: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.019 (harvest_yards_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "harvest_yards_clear_of_paddies",
            not in_paddy,
            f"threshing yard footprint(s) sit IN a flooded paddy: {in_paddy[:3]} - the yard is dry ground; keep its whole footprint clear of every field outline",
        )
    return _kept(locals(), ())


# the yard abuts its OWN farmhouse (intentional, overlap-exempt) but must touch NOTHING else -
# not another farmhouse, a shop, a civic building, or a kura (parent matched by `of`). This is
# the dedicated guard the exemption would otherwise skip - a feature placed before the yard
# (a shop) OR after it (a hand-placed building) must not end up under it.


def _seg_0285_020__k(*, M: Any = _UNBOUND, k: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.020 (k, others, s) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        others = [s for k in _OVERLAP_STRUCTS for s in M.get(k, [])] + M.get("storehouses", []) + M.get("merchant_estates", [])
    return _kept(locals(), ('k', 'others', 's'))


def _seg_0285_021__fouled(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.021 (fouled) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        fouled = []  # type: ignore[var-annotated]
    return _kept(locals(), ('fouled',))


def _seg_0285_022__fouled_1(
    *, fouled: Any = _UNBOUND, others: Any = _UNBOUND, par: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND, t: Any = _UNBOUND, tc: Any = _UNBOUND, yards: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.022 (fouled, par, s, t) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for t in yards:
            tc = rect_corners(_struct_rect(t))
            par = (round(t["of"][0]), round(t["of"][1]))
            for s in others:
                if (round(s["x"]), round(s["y"])) == par:
                    continue
                if abs(s["x"] - t["x"]) + abs(s["y"] - t["y"]) > 140:
                    continue
                if sat_overlap(tc, rect_corners(_struct_rect(s))):
                    fouled.append((round(t["x"]), round(t["y"])))
                    break
    return _kept(locals(), ('fouled', 'par', 's', 't', 'tc'))


def _seg_0285_023__harvest_yards_clear_of_structures(*, check: Any = _UNBOUND, fouled: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.023 (harvest_yards_clear_of_structures) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("harvest_yards_clear_of_structures", not fouled, f"threshing yard(s) overlap a building other than their own farmhouse: {fouled[:3]} - a yard abuts only its own house")
    return _kept(locals(), ())


# ATTACHED KURA STOREHOUSE: a farm's fireproof grain store is drawn as an annex on the house's back
# wall, so every one that exists must ABUT a farmhouse - never float detached in the courtyard (that
# reads as a shed nobody owns). ~30% of farms carry one (a wealth marker), so it is not REQUIRED, but
# any present must be attached. Guards the regression where a move-procedure strands the shed.


def _seg_0285_024__sheds(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.024 (sheds) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        sheds = M.get("farm_sheds", [])
    return _kept(locals(), ('sheds',))


def _seg_0285_025__farm_sheds_attached(
    *, M: Any = _UNBOUND, check: Any = _UNBOUND, h: Any = _UNBOUND, scale: Any = _UNBOUND, sd: Any = _UNBOUND, sheds: Any = _UNBOUND, stranded: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.025 (farm_sheds_attached) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and sheds and M.get("houses"):
        stranded = []
        for sd in sheds:
            if not any(within_edge_gap(sd, h, 10) for h in M["houses"]):  # 10 px of true daylight; two half-diagonals used to stand in for the two extents
                stranded.append((round(sd["x"]), round(sd["y"])))
        check(
            "farm_sheds_attached",
            not stranded,
            f"{len(stranded)} farm storehouse(s) detached from any farmhouse at {stranded[:4]} - a kura is an annex on the house's back wall; draw it WITH the house so a move cannot strand it",
        )
    return _kept(locals(), ('h', 'sd', 'stranded'))


# DOORYARD KITCHEN GARDEN (saien). Every farmstead kept a small intensive vegetable plot for
# the household's daily greens - as universal as the work yard, so EVERY farmhouse must have one
# (a firm 100%, guaranteed by making the garden integral to farmstead placement). It sits on a
# sunny SIDE (preferring the east kitchen end), NOT the north shade and NOT the south front (the
# threshing apron's ground), is SMALLER than the farmhouse, stays on DRY ground off the paddies,
# and abuts only its own house. (Why a side, not the south front: settlements.md "Dooryard gardens".)


def _seg_0285_026__gardens(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.026 (gardens) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        gardens = M.get("gardens", [])
    return _kept(locals(), ('gardens',))


def _seg_0285_027__g_without(*, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, h: Any = _UNBOUND, occ_h: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.027 (g_without, gd, h) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_without = [(round(h["x"]), round(h["y"])) for h in occ_h if not any(gd["of"][0] == h["x"] and gd["of"][1] == h["y"] for gd in gardens)]
    return _kept(locals(), ('g_without', 'gd', 'h'))


def _seg_0285_028__gardens_present(*, check: Any = _UNBOUND, g_without: Any = _UNBOUND, occ_h: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.028 (gardens_present) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_present",
            not g_without,
            f"a {scale} farmstead kept a dooryard kitchen garden for the household's vegetables, and it "
            f"was universal: {len(g_without)} of {len(occ_h)} farmhouses have NO garden {g_without[:3]} - "
            f"every farmhouse must have one (placement makes the garden integral to the farmstead)",
        )
    return _kept(locals(), ())


def _seg_0285_029__g_oversize(*, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, hmap: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.029 (g_oversize, gd) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_oversize = [(round(gd["x"]), round(gd["y"])) for gd in gardens if gd["w"] * gd["h"] >= hmap.get((round(gd["of"][0]), round(gd["of"][1])), 0)]
    return _kept(locals(), ('g_oversize', 'gd'))


def _seg_0285_030__gardens_smaller_than_farmhouse(*, check: Any = _UNBOUND, g_oversize: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.030 (gardens_smaller_than_farmhouse) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("gardens_smaller_than_farmhouse", not g_oversize, f"kitchen garden(s) are not smaller than their farmhouse: {g_oversize[:3]} - the saien is a small dooryard plot, not a field")
    return _kept(locals(), ())


def _seg_0285_031__g_shady(*, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.031 (g_shady, gd) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_shady = [(round(gd["x"]), round(gd["y"])) for gd in gardens if gd["y"] < gd["of"][1] - 5]
    return _kept(locals(), ('g_shady', 'gd'))


def _seg_0285_032__gardens_on_sunny_side(*, check: Any = _UNBOUND, g_shady: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.032 (gardens_on_sunny_side) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_on_sunny_side",
            not g_shady,
            f"kitchen garden(s) sit on the shady NORTH/back side of their farmhouse: {g_shady[:3]} - the saien belongs on a SUNNY side (the east kitchen end, or west), never the cold north back",
        )
    return _kept(locals(), ())


def _seg_0285_033__g_in_paddy(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.033 (g_in_paddy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_in_paddy = []  # type: ignore[var-annotated]
    return _kept(locals(), ('g_in_paddy',))


def _seg_0285_034__e_1(
    *,
    e: Any = _UNBOUND,
    fc: Any = _UNBOUND,
    fields_ol: Any = _UNBOUND,
    g_in_paddy: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    gd: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.034 (e, fc, g_in_paddy, gd) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            fc = rect_corners(_struct_rect(gd))
            if any(
                any(point_in_poly(px, py, ol) for px, py in fc)
                or any(point_in_poly(vx, vy, fc) for vx, vy in ol)
                or any(segments_cross(fc[e], fc[(e + 1) % 4], ol[k], ol[(k + 1) % len(ol)]) for e in range(4) for k in range(len(ol)))
                for ol in fields_ol
            ):
                g_in_paddy.append((round(gd["x"]), round(gd["y"])))
    return _kept(locals(), ('e', 'fc', 'g_in_paddy', 'gd', 'k', 'ol', 'px', 'py', 'vx', 'vy'))


def _seg_0285_035__gardens_clear_of_paddies(*, check: Any = _UNBOUND, g_in_paddy: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.035 (gardens_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_clear_of_paddies",
            not g_in_paddy,
            f"kitchen garden footprint(s) sit IN a flooded paddy: {g_in_paddy[:3]} - the saien is dry ground; keep its whole footprint clear of every field outline",
        )
    return _kept(locals(), ())


# ... and off the IRRIGATION LINES too: the feeder CHANNELS, the in-field/drain DITCHES, and any
# STREAM. A raised-bed vegetable plot cannot sit in a running ditch; `gardens_clear_of_paddies`
# covers the flooded basin, but a feeder channel or the drain ditch threads the DRY village margin
# where the gardens are, so test each garden footprint against every water polyline (its own
# half-width + a little). Same full-footprint test used for structures vs a channel/stream.


def _seg_0285_036__c(*, M: Any = _UNBOUND, c: Any = _UNBOUND, d: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.036 (c, d, st, waterlines) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        waterlines = (
            [(c["poly"], c.get("w", 2.5) / 2 + 3) for c in M.get("channels", [])]
            + [(d["poly"], d.get("w", 7) / 2 + 3) for d in M.get("field_ditches", [])]
            + [(st["poly"], st.get("w", 9) / 2 + 3) for st in M.get("streams", [])]
        )
    return _kept(locals(), ('c', 'd', 'st', 'waterlines'))


def _seg_0285_037__g_on_water(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.037 (g_on_water) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_on_water = []  # type: ignore[var-annotated]
    return _kept(locals(), ('g_on_water',))


def _seg_0285_038__cx(
    *,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    e: Any = _UNBOUND,
    g_on_water: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    gc: Any = _UNBOUND,
    gd: Any = _UNBOUND,
    k: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    waterlines: Any = _UNBOUND,
    whw: Any = _UNBOUND,
    wp: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.038 (cx, cy, e, g_on_water) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            gc = rect_corners(_struct_rect(gd))
            for wp, whw in waterlines:
                if (
                    any(seg_dist(cx, cy, wp[k], wp[k + 1]) < whw for cx, cy in gc for k in range(len(wp) - 1))
                    or any(point_in_poly(wx, wy, gc) for wx, wy in wp)
                    or any(segments_cross(wp[k], wp[k + 1], gc[e], gc[(e + 1) % 4]) for k in range(len(wp) - 1) for e in range(4))
                ):
                    g_on_water.append((round(gd["x"]), round(gd["y"])))
                    break
    return _kept(locals(), ('cx', 'cy', 'e', 'g_on_water', 'gc', 'gd', 'k', 'whw', 'wp', 'wx', 'wy'))


def _seg_0285_039__gardens_clear_of_channels(*, check: Any = _UNBOUND, g_on_water: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.039 (gardens_clear_of_channels) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_clear_of_channels",
            not g_on_water,
            f"kitchen garden(s) overlap an irrigation channel/ditch: {g_on_water[:3]} - a raised-bed saien sits on dry ground, never in a running feeder channel, field ditch, or stream",
        )
    return _kept(locals(), ())


def _seg_0285_040__g_fouled(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.040 (g_fouled) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_fouled = []  # type: ignore[var-annotated]
    return _kept(locals(), ('g_fouled',))


def _seg_0285_041__g_fouled_1(
    *, g_fouled: Any = _UNBOUND, gardens: Any = _UNBOUND, gc: Any = _UNBOUND, gd: Any = _UNBOUND, others: Any = _UNBOUND, par: Any = _UNBOUND, s: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.041 (g_fouled, gc, gd, par) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            gc = rect_corners(_struct_rect(gd))
            par = (round(gd["of"][0]), round(gd["of"][1]))
            for s in others:
                if (round(s["x"]), round(s["y"])) == par:
                    continue
                if abs(s["x"] - gd["x"]) + abs(s["y"] - gd["y"]) > 140:
                    continue
                if sat_overlap(gc, rect_corners(_struct_rect(s))):
                    g_fouled.append((round(gd["x"]), round(gd["y"])))
                    break
    return _kept(locals(), ('g_fouled', 'gc', 'gd', 'par', 's'))


def _seg_0285_042__gardens_clear_of_structures(*, check: Any = _UNBOUND, g_fouled: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.042 (gardens_clear_of_structures) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("gardens_clear_of_structures", not g_fouled, f"kitchen garden(s) overlap a building other than their own farmhouse: {g_fouled[:3]} - a garden abuts only its own house")
    return _kept(locals(), ())


# the garden and the farmhouse's STOREHOUSE/shed must never overlap - the shed sits on a wall the
# garden does not use (west for a dispersed farm, the shaded north for a nucleated one). The shed is
# a recorded annex (M['farm_sheds']), so read its actual footprint straight from there.


def _seg_0285_043__sheds_1(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.043 (sheds) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        sheds = M.get("farm_sheds", [])
    return _kept(locals(), ('sheds',))


def _seg_0285_044__g_on_shed(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.044 (g_on_shed) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_on_shed = []  # type: ignore[var-annotated]
    return _kept(locals(), ('g_on_shed',))


def _seg_0285_045__g_on_shed_1(
    *, g_on_shed: Any = _UNBOUND, gardens: Any = _UNBOUND, gc: Any = _UNBOUND, gd: Any = _UNBOUND, scale: Any = _UNBOUND, sd: Any = _UNBOUND, sheds: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.045 (g_on_shed, gc, gd, sd) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            gc = rect_corners(_struct_rect(gd))
            for sd in sheds:
                if abs(sd["x"] - gd["x"]) + abs(sd["y"] - gd["y"]) > 120:
                    continue
                if sat_overlap(gc, rect_corners(sd)):
                    g_on_shed.append((round(gd["x"]), round(gd["y"])))
                    break
    return _kept(locals(), ('g_on_shed', 'gc', 'gd', 'sd'))


def _seg_0285_046__gardens_clear_of_sheds(*, check: Any = _UNBOUND, g_on_shed: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.046 (gardens_clear_of_sheds) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_clear_of_sheds",
            not g_on_shed,
            f"kitchen garden(s) overlap a farmhouse's storehouse/shed: {g_on_shed[:3]} - the shed sits on the "
            f"house's WEST side and the garden on a sunny (east-preferred) side, so the two must never collide",
        )
    return _kept(locals(), ())


# A dooryard bed and a threshing yard were HAND-worked plots bent to paths and soil, not surveyed
# rectangles - the generator draws each as a slightly-irregular 4-sided quad (a garden more irregular,
# a swept work yard near-square). Validate the SHAPE it records: every garden/yard with a `poly` must
# carry exactly 4 vertices, be non-degenerate (real area), and stay INSCRIBED in its recorded w x h
# bounds (the jitter only pulls corners INWARD, so a poly poking outside its rect means the overlap
# checks - which use that rect - were cleared against the wrong footprint). WHY quads: settlements.md
# "Dooryard kitchen gardens" / "Threshing yards" (irregular-plot grounding).


def _seg_0285_047__bad_quad(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.047 (bad_quad) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        bad_quad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('bad_quad',))


def _seg_0285_048__bad_quad_1(
    *,
    bad_quad: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    inside: Any = _UNBOUND,
    pg: Any = _UNBOUND,
    pl: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    yards: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.048 (bad_quad, hh, hw, inside) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for pl in gardens + yards:
            pg = pl.get("poly")
            if pg is None:
                continue  # legacy rect-only record (dispersed maps predate poly)
            hw, hh = pl["w"] / 2 + 0.6, pl["h"] / 2 + 0.6  # small tolerance for rounding
            inside = all(abs(px - pl["x"]) <= hw and abs(py - pl["y"]) <= hh for px, py in pg)
            if len(pg) != 4 or poly_area(pg) < 0.20 * pl["w"] * pl["h"] or not inside:
                bad_quad.append((round(pl["x"]), round(pl["y"])))
    return _kept(locals(), ('bad_quad', 'hh', 'hw', 'inside', 'pg', 'pl', 'px', 'py'))


def _seg_0285_049__garden_plots_are_quads(*, bad_quad: Any = _UNBOUND, check: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.049 (garden_plots_are_quads) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "garden_plots_are_quads",
            not bad_quad,
            f"garden/yard footprint(s) are not valid inscribed 4-gons: {bad_quad[:3]} - each is a slightly-irregular quadrilateral (4 vertices, real area) that stays within its reserved w x h rect",
        )
    return _kept(locals(), ())


# GARDEN AREA is held to a HISTORICAL band. Unlike the house/yard (drawn oversized against the
# fields for legibility), a dooryard kitchen garden at 1 px = 2 ft is near its TRUE size, so its area
# is a real quantity we can check against the ground a household could hand-work. The saien is the
# small intensive daily-greens bed by the kitchen (the bulk vegetable growing was out in the hatake
# dry fields, not here): historically a few tsubo up to ~1.4 se - roughly 10-140 m^2 (1 tsubo = 3.31
# m^2; 1 se = 30 tsubo ~ 99 m^2). We sum ALL of a household's garden beds (a fragmented plot is still
# one household's garden) and require the TOTAL in that band. WHY the numbers: settlements.md "Dooryard
# kitchen gardens" (area grounding). Scale override via meta.ft_per_px for any non-standard map.


def _seg_0285_050__ft_per_px(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.050 (ft_per_px) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        ft_per_px = float(meta.get("ftpx") or meta.get("ft_per_px") or 2.0)  # the map's real scale (village 2, hamlet 1)
    return _kept(locals(), ('ft_per_px',))


def _seg_0285_051__m2_per_px2(*, ft_per_px: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.051 (m2_per_px2) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        m2_per_px2 = (ft_per_px * 0.3048) ** 2  # ft/px -> m per px, squared -> m^2 per px^2
    return _kept(locals(), ('m2_per_px2',))


def _seg_0285_052__GARDEN_M2_MAX(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.052 (GARDEN_M2_MAX, GARDEN_M2_MIN) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        GARDEN_M2_MIN, GARDEN_M2_MAX = 10.0, 140.0
    return _kept(locals(), ('GARDEN_M2_MAX', 'GARDEN_M2_MIN'))


def _seg_0285_053__by_house(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.053 (by_house) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        by_house: dict[tuple[int, int], float] = {}  # type: ignore[no-redef,unused-ignore]
    return _kept(locals(), ('by_house',))


def _seg_0285_054__a_px(
    *, a_px: Any = _UNBOUND, by_house: Any = _UNBOUND, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, key: Any = _UNBOUND, pg: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.054 (a_px, by_house, gd, key) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gd in gardens:
            pg = gd.get("poly")
            a_px = poly_area(pg) if pg else gd["w"] * gd["h"]
            key = (round(gd["of"][0]), round(gd["of"][1]))
            by_house[key] = by_house.get(key, 0.0) + a_px
    return _kept(locals(), ('a_px', 'by_house', 'gd', 'key', 'pg'))


def _seg_0285_055__a_px_1(
    *,
    GARDEN_M2_MAX: Any = _UNBOUND,
    GARDEN_M2_MIN: Any = _UNBOUND,
    a_px: Any = _UNBOUND,
    by_house: Any = _UNBOUND,
    hx: Any = _UNBOUND,
    hy: Any = _UNBOUND,
    m2_per_px2: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.055 (a_px, g_area_bad, hx, hy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_area_bad = [(hx, hy, round(a_px * m2_per_px2)) for (hx, hy), a_px in by_house.items() if not (GARDEN_M2_MIN <= a_px * m2_per_px2 <= GARDEN_M2_MAX)]
    return _kept(locals(), ('a_px', 'g_area_bad', 'hx', 'hy'))


def _seg_0285_056__garden_area_within_norms(
    *, GARDEN_M2_MAX: Any = _UNBOUND, GARDEN_M2_MIN: Any = _UNBOUND, check: Any = _UNBOUND, g_area_bad: Any = _UNBOUND, scale: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.056 (garden_area_within_norms) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "garden_area_within_norms",
            not g_area_bad,
            f"household kitchen-garden total area out of the historical band "
            f"[{GARDEN_M2_MIN:.0f}-{GARDEN_M2_MAX:.0f} m^2]: {g_area_bad[:3]} (x, y, m^2) - a saien is the small "
            f"intensive daily-greens bed by the kitchen, ~a few tsubo up to ~1.4 se; bigger reads as a field, "
            f"tinier as no garden at all",
        )
    return _kept(locals(), ())


# HOMESTEAD GROVE (yashikirin) - the farmhouse windbreak. A dense L-BELT of shelter trees on the
# WINDWARD side(s) of the house (one record per belt ARM), blocking the cold prevailing wind while
# leaving the SUNNY lee open. Default windward NW: the East Asian winter monsoon blows NW across
# China and Japan alike, so N+W is windward, S/E the sheltered sunny side - a map keys it off its
# own geography with meta(windward=...). The grove is NEAR-UNIVERSAL (meta.grove_prevalence) and
# the LARGEST homestead appurtenance - bigger than the house. We gate GEOMETRY per arm (windward,
# off the paddy, off other buildings), the typical grove's SCALE (groves_are_substantial), a
# presence FLOOR scaled to the knob, and (city) that NO intramural farm carries one. WHY (the ~30-40
# tree stand, the windward rule, the firewood/timber/bamboo it gave): settlements.md "Homestead groves".


def _seg_0285_057__groves(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.057 (groves) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        groves = M.get("groves", [])
    return _kept(locals(), ('groves',))


def _seg_0285_058__grove_of(*, groves: Any = _UNBOUND, gv: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.058 (grove_of, gv) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        grove_of = {(round(gv["of"][0]), round(gv["of"][1])) for gv in groves}  # distinct farms with a grove
    return _kept(locals(), ('grove_of', 'gv'))


def _seg_0285_059__WINDV(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.059 (WINDV) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        WINDV = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0), "NW": (-1, -1), "NE": (1, -1), "SW": (-1, 1), "SE": (1, 1)}
    return _kept(locals(), ('WINDV',))


def _seg_0285_060__windward(*, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.060 (windward) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        windward = str(meta.get("windward", "NW")).upper().strip()
    return _kept(locals(), ('windward',))


def _seg_0285_061__wvx(*, WINDV: Any = _UNBOUND, scale: Any = _UNBOUND, windward: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.061 (wvx, wvy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        wvx, wvy = WINDV.get(windward, (-1, -1))
    return _kept(locals(), ('wvx', 'wvy'))


def _seg_0285_062__g_lee(*, groves: Any = _UNBOUND, gv: Any = _UNBOUND, scale: Any = _UNBOUND, wvx: Any = _UNBOUND, wvy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.062 (g_lee, gv) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_lee = [(round(gv["x"]), round(gv["y"])) for gv in groves if (gv["x"] - gv["of"][0]) * wvx + (gv["y"] - gv["of"][1]) * wvy <= 0]
    return _kept(locals(), ('g_lee', 'gv'))


def _seg_0285_063__groves_on_windward_side(*, check: Any = _UNBOUND, g_lee: Any = _UNBOUND, scale: Any = _UNBOUND, windward: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.063 (groves_on_windward_side) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "groves_on_windward_side",
            not g_lee,
            f"homestead grove(s) sit on the LEE/sunny side of their farmhouse, not the windward {windward}: "
            f"{g_lee[:3]} - a yashikirin shelters the windward wall (default N/W) and leaves the sunny lee open",
        )
    return _kept(locals(), ())


def _seg_0285_064__g_in_paddy_1(*, fields_ol: Any = _UNBOUND, groves: Any = _UNBOUND, gv: Any = _UNBOUND, ol: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.064 (g_in_paddy, gv, ol) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_in_paddy = [(round(gv["x"]), round(gv["y"])) for gv in groves if any(point_in_poly(gv["x"], gv["y"], ol) for ol in fields_ol)]
    return _kept(locals(), ('g_in_paddy', 'gv', 'ol'))


def _seg_0285_065__groves_clear_of_paddies(*, check: Any = _UNBOUND, g_in_paddy: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.065 (groves_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "groves_clear_of_paddies",
            not g_in_paddy,
            f"homestead grove(s) sit squarely IN a flooded paddy (center over water): {g_in_paddy[:3]} - the "
            f"windbreak HUGS the bund (abutting/overlapping the field edge is correct) but must not be planted "
            f"out in the paddy itself",
        )
    return _kept(locals(), ())


def _seg_0285_066__gr_fouled(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.066 (gr_fouled) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        gr_fouled = []  # type: ignore[var-annotated]
    return _kept(locals(), ('gr_fouled',))


def _seg_0285_067__gc(
    *,
    gc: Any = _UNBOUND,
    gci: Any = _UNBOUND,
    gr_fouled: Any = _UNBOUND,
    groves: Any = _UNBOUND,
    gv: Any = _UNBOUND,
    others: Any = _UNBOUND,
    par: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.067 (gc, gci, gr_fouled, gv) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for gv in groves:
            gci = dict(gv)
            gci["w"] = gv["w"] * 0.7
            gci["h"] = gv["h"] * 0.7  # inset: tolerate abutting
            gc = rect_corners(_struct_rect(gci))
            par = (round(gv["of"][0]), round(gv["of"][1]))
            for s in others:
                if (round(s["x"]), round(s["y"])) == par:
                    continue
                if abs(s["x"] - gv["x"]) + abs(s["y"] - gv["y"]) > 140:
                    continue
                if sat_overlap(gc, rect_corners(_struct_rect(s))):
                    gr_fouled.append((round(gv["x"]), round(gv["y"])))
                    break
    return _kept(locals(), ('gc', 'gci', 'gr_fouled', 'gv', 'par', 's'))


def _seg_0285_068__groves_clear_of_structures(*, check: Any = _UNBOUND, gr_fouled: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.068 (groves_clear_of_structures) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check("groves_clear_of_structures", not gr_fouled, f"homestead grove(s) overlap a building other than their own farmhouse: {gr_fouled[:3]} - a grove abuts only its own house")
    return _kept(locals(), ())


# SUN: a threshing yard dries rice in the SOUTHERN sun, so no grove may sit in the strip directly
# SOUTH of a yard (a neighbor's grove there would shade it). A grove is N/W of its OWN house, far
# from its own yard's southern corridor, so this only catches a grove shading a NEIGHBOR's yard.


def _seg_0285_069__shaded(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.069 (shaded) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        shaded = []  # type: ignore[var-annotated]
    return _kept(locals(), ('shaded',))


def _seg_0285_070__cyx(
    *, cyx: Any = _UNBOUND, cyy: Any = _UNBOUND, groves: Any = _UNBOUND, gv: Any = _UNBOUND, scale: Any = _UNBOUND, shaded: Any = _UNBOUND, yards: Any = _UNBOUND, yd: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 0285.070 (cyx, cyy, gv, shaded) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for yd in yards:
            cyx, cyy = yd["x"], yd["y"] + yd["h"] / 2 + 11  # the ~22px sun-corridor just south of the yard
            if any(abs(gv["x"] - cyx) < (gv["w"] + yd["w"]) / 2 and abs(gv["y"] - cyy) < (gv["h"] + 22) / 2 for gv in groves):
                shaded.append((round(yd["x"]), round(yd["y"])))
    return _kept(locals(), ('cyx', 'cyy', 'gv', 'shaded', 'yd'))


# ...AND NOT BY A NEIGHBOUR'S FARMHOUSE, which is the taller obstacle and was never
# tested (GM 2026-08-13: "would the shadow from the farmhouse directly to the south
# block too much light?"). Researched in research/homesteads.md, "The threshing yard's
# sun": thatch is pitched 45 deg or steeper, so the 46x28 ft minka's ridge stands ~20 ft
# up, and at 38N in the 10th month that throws 21 ft of shadow at noon and 39 ft by 9am.
# 39 ft is the rule, because the drying day that matters is 9-to-3.
#
# GATED ON `meta.generated_by`, and that gate IS the GM's decision (2026-08-13). Every
# hand-authored nucleated map in the pool breaks this - Ueda has 45 of 85 yards shaded at
# noon, Hoshigaoka 31 of 70, Ubame 21 of 36, with neighbours' walls 2-8 ft off the yard
# edge - and re-packing them all was judged the wrong trade. Instead the rule binds the
# SCRIPTED path, and each legacy map inherits it at the moment it is converted to a
# generator. The exemption therefore cannot rot: it is not a list anyone has to prune,
# it is the absence of a tag that conversion adds.


def _seg_0285_071__yards_unshaded_by_neighbors(
    *,
    check: Any = _UNBOUND,
    gap: Any = _UNBOUND,
    hh_: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nshade: Any = _UNBOUND,
    par: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    sun_ft: Any = _UNBOUND,
    sun_ftpx: Any = _UNBOUND,
    yards: Any = _UNBOUND,
    yd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.071 (yards_unshaded_by_neighbors) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and meta.get("generated_by"):
        sun_ft = 39.0
        sun_ftpx = float(meta.get("ftpx") or 1)  # derived locally: `ftpx` is bound conditionally in this scope
        nshade = []
        for yd in yards:
            par = yd.get("of")
            for hh_ in houses:
                if par and abs(hh_["x"] - par[0]) < 1 and abs(hh_["y"] - par[1]) < 1:
                    continue  # its own house is NORTH of it by construction
                if abs(hh_["x"] - yd["x"]) >= (hh_["w"] + yd["w"]) / 2:
                    continue  # not in the yard's sun corridor
                gap = ((hh_["y"] - hh_["h"] / 2) - (yd["y"] + yd["h"] / 2)) * sun_ftpx
                if 0 < gap < sun_ft:
                    nshade.append((round(yd["x"]), round(yd["y"])))
                    break
        check(
            "yards_unshaded_by_neighbors",
            not nshade,
            f"threshing yard(s) {nshade[:3]} stand within {sun_ft:.0f} ft of a NEIGHBOUR's farmhouse to their "
            f"SOUTH - a minka's ~20 ft ridge throws 21 ft of shadow at noon in the threshing month and 39 ft by "
            f"9am, so that yard loses the drying day. Keep the sun corridor south of every yard clear of houses "
            f"(the placer does it with s.sun_corridor(39)); a yard may also stagger east or west out of the shadow",
        )
    return _kept(locals(), ('gap', 'hh_', 'nshade', 'par', 'sun_ft', 'sun_ftpx', 'yd'))


def _seg_0285_072__yards_unshaded_by_groves(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, shaded: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.072 (yards_unshaded_by_groves) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "yards_unshaded_by_groves",
            not shaded,
            f"threshing yard(s) {shaded[:3]} have a grove in the sun-corridor just to their SOUTH - it would shade the drying ground; keep groves out of the strip south of any yard",
        )
    return _kept(locals(), ())


# SAME sun rule for the COMMUNAL fengshui trees: no village-grove CLUMP may sit in the southern sun-
# corridor of a threshing yard OR a kitchen garden (both need the drying/growing sun from the south).
# The scatter records its real clumps, so test those, not the bounding poly. WHY: settlements.md 'Village windbreak'.


def _seg_0285_073__cx_1(*, M: Any = _UNBOUND, cx: Any = _UNBOUND, cy: Any = _UNBOUND, g: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.073 (cx, cy, g, vg_clumps) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vg_clumps = [(cx, cy, g.get("r", 6)) for g in M.get("village_groves", []) for cx, cy in g.get("clumps", [])]
    return _kept(locals(), ('cx', 'cy', 'g', 'vg_clumps'))


def _seg_0285_074__vg_shaded(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.074 (vg_shaded) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vg_shaded = []  # type: ignore[var-annotated]
    return _kept(locals(), ('vg_shaded',))


def _seg_0285_075__cx_2(
    *,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    f: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    r: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    se: Any = _UNBOUND,
    vg_clumps: Any = _UNBOUND,
    vg_shaded: Any = _UNBOUND,
    yards: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.075 (cx, cy, f, r) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for f in yards + gardens:
            se = f["y"] + f["h"] / 2
            if any(abs(cx - f["x"]) < f["w"] / 2 + r and se - r < cy < se + 22 + r for cx, cy, r in vg_clumps):
                vg_shaded.append((round(f["x"]), round(f["y"])))
    return _kept(locals(), ('cx', 'cy', 'f', 'r', 'se', 'vg_shaded'))


def _seg_0285_076__village_trees_unshade_yards_and_gardens(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, vg_shaded: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.076 (village_trees_unshade_yards_and_gardens) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "village_trees_unshade_yards_and_gardens",
            not vg_shaded,
            f"a village-grove tree sits in the southern sun-corridor of yard/garden(s) {vg_shaded[:3]} - it would "
            f"shade the drying/growing ground; keep the scatter + belts out of the strip south of any yard or garden",
        )
    return _kept(locals(), ())


# EAST SUN (option): a kitchen garden on a house's lee/EAST side loses its MORNING sun if a neighbor's
# grove arm (or a copse) stands hard against its east. Where a small SOUTHWARD nudge into open ground
# would clear it (the tree then falls to the garden's NE), the placement takes it (_relax_gardens_south).
# This fires ONLY on an AVOIDABLE case - a garden still east-shaded though a clear south-shift existed -
# so a garden genuinely boxed in to the south (paddy/lane/neighbor) is exempt. WHY: settlements.md 'gardens'.
# scoped to the BUNDLE-path farmsteads (villages + to-scale hamlets), where _relax_gardens_south runs;
# a town/city places its outside farms on the legacy path (no south-nudge), so the rule does not apply.


def _seg_0285_077__gardens_unshaded_from_east(
    *,
    M: Any = _UNBOUND,
    _band: Any = _UNBOUND,
    _bed_clear: Any = _UNBOUND,
    _bog: Any = _UNBOUND,
    _e_iv: Any = _UNBOUND,
    _fol: Any = _UNBOUND,
    _hh: Any = _UNBOUND,
    _hill: Any = _UNBOUND,
    _lanes: Any = _UNBOUND,
    _pond: Any = _UNBOUND,
    _shaded: Any = _UNBOUND,
    _water: Any = _UNBOUND,
    a: Any = _UNBOUND,
    b: Any = _UNBOUND,
    box: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    dy: Any = _UNBOUND,
    east_bad: Any = _UNBOUND,
    f: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    gd: Any = _UNBOUND,
    gh: Any = _UNBOUND,
    groves: Any = _UNBOUND,
    gv: Any = _UNBOUND,
    gw: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    hh: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    iv: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    m: Any = _UNBOUND,
    maxshift: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    own: Any = _UNBOUND,
    p: Any = _UNBOUND,
    r: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    vg_clumps: Any = _UNBOUND,
    wp: Any = _UNBOUND,
    yards: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.077 (gardens_unshaded_from_east) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and groves and meta.get("toscale", scale == "village"):
        _band = 22
        _hh = {(round(h["x"]), round(h["y"])): h["h"] for h in houses}
        _lanes = M.get("lanes", [])
        _bog = [m["poly"] for m in M.get("marshes", []) if m.get("role") != "pond_fringe" and m.get("poly")]
        _water = [c["poly"] for c in M.get("channels", [])] + [st["poly"] for st in M.get("streams", [])]
        _fol = [f["outline"] for f in M.get("fields", []) if f.get("outline")]
        _hill, _pond = M.get("hill"), M.get("pond")

        def _e_iv(ge: float, own: tuple[float, ...]) -> list[tuple[float, float]]:
            iv = [(gv["y"] - gv["h"] / 2, gv["y"] + gv["h"] / 2) for gv in groves if tuple(gv.get("of", [])) != own and ge - 2 <= gv["x"] - gv["w"] / 2 < ge + _band]
            iv += [(cy - r, cy + r) for cx, cy, r in vg_clumps if ge - 2 <= cx - r < ge + _band]
            return iv

        def _shaded(lane: tuple[float, float], iv: list[tuple[float, float]]) -> bool:
            return any(a < lane[1] and lane[0] < b for a, b in iv)

        def _bed_clear(bx: float, by: float, bw: float, bh: float, own: tuple[float, ...]) -> bool:
            box = (bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2)
            for h in houses:
                if (round(h["x"]), round(h["y"])) != (round(own[0]), round(own[1])) and abs(bx - h["x"]) < (bw + h["w"]) / 2 and abs(by - h["y"]) < (bh + h["h"]) / 2:
                    return False
            for s in yards + groves + gardens + M.get("farm_sheds", []) + M.get("byres", []):
                if tuple(s.get("of", [])) == own:  # skip the garden's OWN yard/grove/beds/shed
                    continue
                if abs(bx - s["x"]) < (bw + s["w"]) / 2 and abs(by - s["y"]) < (bh + s["h"]) / 2:
                    return False
            if any(_box_hits_poly(box, ol) for ol in _fol) or any(_box_hits_poly(box, p) for p in _bog):
                return False
            for ln in _lanes:
                p = ln["pts"]
                if any(seg_dist(bx, by, p[k], p[k + 1]) < ln.get("w", 6) / 2 + 2 for k in range(len(p) - 1)):
                    return False
            for wp in _water:
                if any(seg_dist(bx, by, wp[k], wp[k + 1]) < 6 for k in range(len(wp) - 1)):
                    return False
            return not ((_hill and in_ellipse(bx, by, _hill)) or (_pond and in_ellipse(bx, by, _pond)))

        east_bad = []
        for gd in gardens:
            gx, gy, gw, gh = gd["x"], gd["y"], gd["w"], gd["h"]
            own = tuple(gd.get("of", []))
            iv = _e_iv(gx + gw / 2, own)
            if not _shaded((gy - gh / 2, gy + gh / 2), iv):
                continue  # not currently east-shaded
            hh = _hh.get((round(own[0]), round(own[1])), gh) if own else gh
            maxshift, dy = gh + hh + 6, 4
            while dy <= maxshift:
                if not _shaded((gy + dy - gh / 2, gy + dy + gh / 2), iv) and _bed_clear(gx, gy + dy, gw, gh, own):
                    east_bad.append((round(gx), round(gy)))  # a clear south-shift existed -> avoidable
                    break
                dy += 4
        check(
            "gardens_unshaded_from_east",
            not east_bad,
            f"kitchen garden(s) {east_bad[:4]} sit with a tree hard against their EAST (losing the morning sun) "
            f"though a small SOUTHWARD shift into open ground would clear it - nudge the garden south of the "
            f"tree (the placement's _relax_gardens_south does this; a garden truly boxed in south is exempt)",
        )
    return _kept(
        locals(),
        (
            '_band',
            '_bed_clear',
            '_bog',
            '_e_iv',
            '_fol',
            '_hh',
            '_hill',
            '_lanes',
            '_pond',
            '_shaded',
            '_water',
            'c',
            'dy',
            'east_bad',
            'f',
            'gd',
            'gh',
            'gw',
            'gx',
            'gy',
            'h',
            'hh',
            'iv',
            'm',
            'maxshift',
            'own',
            'st',
        ),
    )


# SCALE: the typical grove must read as the LARGEST homestead appurtenance - a real stand of dozens
# of trees, not a clump. The median grove's total footprint (its arms) must be >= ~0.75x the house
# it shelters (the spacious farms run well above; a single-arm grove on a cramped farm pulls the
# median but stays substantial). This catches a regression that shrinks groves back to a few trees.


def _seg_0285_078__groves_are_substantial(
    *,
    a: Any = _UNBOUND,
    check: Any = _UNBOUND,
    gk: Any = _UNBOUND,
    grove_of: Any = _UNBOUND,
    groves: Any = _UNBOUND,
    gsz: Any = _UNBOUND,
    gv: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    hsz: Any = _UNBOUND,
    med: Any = _UNBOUND,
    ratios: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.078 (groves_are_substantial) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and len(grove_of) >= 6:
        hsz = {(round(h["x"]), round(h["y"])): h["w"] * h["h"] for h in houses}
        gsz: dict[tuple[int, int], float] = {}  # type: ignore[no-redef]
        for gv in groves:
            gk = (round(gv["of"][0]), round(gv["of"][1]))
            gsz[gk] = gsz.get(gk, 0) + gv["w"] * gv["h"]
        ratios = sorted(a / hsz[gk] for gk, a in gsz.items() if gk in hsz and hsz[gk])
        med = ratios[len(ratios) // 2]
        check(
            "groves_are_substantial",
            med >= 0.5,
            f"the typical homestead grove is too small (median {med:.2f}x its house) - the spacious farms must "
            f"carry a real stand (a yashikirin is the LARGEST homestead feature); small clumps on cramped farms "
            f"are fine, but a median below half the house means groves shrank back to a few trees everywhere",
        )
    return _kept(locals(), ('a', 'gk', 'gsz', 'gv', 'h', 'hsz', 'med', 'ratios'))


# VISIBLE: the dooryard garden must not be buried under a grove (the homestead solver spaces the
# garden to the LEE side and the grove to the windward, so they never stack). A garden substantially
# overlapped by a grove arm is a regression. WHY: settlements.md "Homestead groves".


def _seg_0285_079__g_buried(*, gardens: Any = _UNBOUND, gd: Any = _UNBOUND, groves: Any = _UNBOUND, gv: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.079 (g_buried, gd, gv) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        g_buried = [
            (round(gd["x"]), round(gd["y"])) for gd in gardens if any(abs(gd["x"] - gv["x"]) < (gd["w"] + gv["w"]) / 2 - 3 and abs(gd["y"] - gv["y"]) < (gd["h"] + gv["h"]) / 2 - 3 for gv in groves)
        ]
    return _kept(locals(), ('g_buried', 'gd', 'gv'))


def _seg_0285_080__gardens_clear_of_groves(*, check: Any = _UNBOUND, g_buried: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.080 (gardens_clear_of_groves) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "gardens_clear_of_groves",
            not g_buried,
            f"kitchen garden(s) {g_buried[:3]} sit under a homestead grove - the solver spaces the garden to the LEE side and the grove to the windward; they must not overlap",
        )
    return _kept(locals(), ())


# WHERE POSSIBLE: a grove is drawn on EVERY farmhouse that has windward room - the yashikirin ringed
# every dispersed farmstead - so a grove-LESS farm must be one whose windward side is genuinely blocked
# (a paddy, a neighbor, or the sun-corridor south of a yard). If a grove-less farm has CLEAR windward
# room, the generator omitted a grove it could have placed. Replaces the old blunt presence floor.


def _seg_0285_081__groves_where_possible(
    *,
    B: Any = _UNBOUND,
    Hm: Any = _UNBOUND,
    M: Any = _UNBOUND,
    WF: Any = _UNBOUND,
    Wm: Any = _UNBOUND,
    avoid: Any = _UNBOUND,
    c: Any = _UNBOUND,
    ch: Any = _UNBOUND,
    check: Any = _UNBOUND,
    clump_clear: Any = _UNBOUND,
    corridors: Any = _UNBOUND,
    crop_ol: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    dpl: Any = _UNBOUND,
    e: Any = _UNBOUND,
    fdx: Any = _UNBOUND,
    fdy: Any = _UNBOUND,
    fields_ol: Any = _UNBOUND,
    gardens: Any = _UNBOUND,
    grove_of: Any = _UNBOUND,
    hh_: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    hw: Any = _UNBOUND,
    hx: Any = _UNBOUND,
    hy: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    min_clump: Any = _UNBOUND,
    n: Any = _UNBOUND,
    ol: Any = _UNBOUND,
    omitted: Any = _UNBOUND,
    others: Any = _UNBOUND,
    par: Any = _UNBOUND,
    perp: Any = _UNBOUND,
    poly: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    s: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    vx: Any = _UNBOUND,
    vy: Any = _UNBOUND,
    windward: Any = _UNBOUND,
    yards: Any = _UNBOUND,
    yd: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.081 (groves_where_possible) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and scale in ("town", "village", "hamlet") and len(houses) >= 10 and not meta.get("nucleated"):
        WF = {
            "N": [((0, -1), 0)],
            "S": [((0, 1), 0)],
            "E": [((1, 0), 0)],
            "W": [((-1, 0), 0)],
            "NW": [((0, -1), -1), ((-1, 0), 0)],
            "NE": [((0, -1), 1), ((1, 0), 0)],
            "SW": [((0, 1), -1), ((-1, 0), 0)],
            "SE": [((0, 1), 1), ((1, 0), 0)],
        }
        avoid = others + gardens + yards + M.get("manors", []) + M.get("religious", [])
        corridors = [c for c in [M.get("lane"), M.get("road")] if c]
        corridors += [(c.get("poly", c) if isinstance(c, dict) else c) for c in M.get("channels", [])]
        corridors += [(s.get("poly", s) if isinstance(s, dict) else s) for s in M.get("streams", [])]
        # a town RAMPART blocks a grove belt exactly like a road: a farm hugging the wall has a
        # wall-shaded windward side (the placement side refuses via the wall's no-build corridor)
        corridors += [M["wall"]] if M.get("wall") else []
        Wm, Hm = meta.get("W", 1820), meta.get("H", 1180)

        def min_clump(hh_: dict[str, Any], fdx: float, fdy: float, perp: float) -> tuple[float, float, float, float]:
            hx, hy, hw, hz = hh_["x"], hh_["y"], hh_["w"], hh_["h"]
            dm = 13 * hw / 44.0  # minimal-clump depth (44 = base house width / bscale)
            if fdy:
                return hx + perp * dm / 2, hy + fdy * (hz / 2 + dm / 2 + 1.5), (hw + dm) * 0.5, dm
            return hx + fdx * (hw / 2 + dm / 2 + 1.5), hy, dm, hz * 0.5

        # B is a CONSERVATIVE margin: the check only claims "room" when the windward side is CLEARLY
        # open (room + B px), so it fires on a gross omission (a farm with plenty of space and no grove)
        # but tolerates the borderline cases where this check can't perfectly mirror the placement test.
        B = 7
        # ALL cropland blocks a grove clump, not just the flooded paddy: the dry hem strips /
        # garden tracts are barley, and trees do not grow in the barley either (the placement
        # side refuses them via dry_polys in _grove_fits) - so a hem-shadowed windward side
        # legitimately leaves a farm grove-less, same as a paddy-shadowed one. LOCAL to this
        # check: the shared fields_ol stays paddy-only (its other uses mean "in the rice").
        crop_ol = fields_ol + [dpl["poly"] for dpl in M.get("dry_plots", [])]

        def clump_clear(cx: float, cy: float, cw: float, ch: float, par: tuple[int, int]) -> bool:
            if cx < 55 or cx > Wm - 55 or cy < 88 or cy > Hm - 26:
                return False
            rc = rect_corners({"x": cx, "y": cy, "w": cw, "h": ch, "rot": 0})
            for ol in crop_ol:
                n = len(ol)
                if (
                    point_in_poly(cx, cy, ol)
                    or edge_dist(cx, cy, ol) < 14 + B  # mirror settlement._in_blocked
                    or any(point_in_poly(px, py, ol) for px, py in rc)
                    or any(point_in_poly(vx, vy, rc) for vx, vy in ol)
                    or any(segments_cross(rc[e], rc[(e + 1) % 4], ol[k], ol[(k + 1) % n]) for e in range(4) for k in range(n))
                ):
                    return False
            for s in avoid:
                if (round(s["x"]), round(s["y"])) == par:
                    continue
                if abs(cx - s["x"]) < (cw + s["w"]) / 2 + B and abs(cy - s["y"]) < (ch + s["h"]) / 2 + B:
                    return False
            for yd in yards:
                if abs(cx - yd["x"]) < (cw + yd["w"]) / 2 + B and abs(cy - (yd["y"] + yd["h"] / 2 + 11)) < (ch + 22) / 2 + B:
                    return False
            return all(not (len(poly) >= 2 and any(seg_dist(cx, cy, poly[k], poly[k + 1]) < 20 + B for k in range(len(poly) - 1))) for poly in corridors)

        omitted = []
        for hh_ in houses:
            if hh_.get("role") == "headman" or hh_.get("kind") == "abandoned":
                continue
            par = (round(hh_["x"]), round(hh_["y"]))
            if par in grove_of:
                continue
            if any(clump_clear(*min_clump(hh_, fdx, fdy, perp), par) for (fdx, fdy), perp in WF.get(windward, WF["NW"])):
                omitted.append(par)
        check(
            "groves_where_possible",
            not omitted,
            f"farm(s) {omitted[:4]} have clear windward room but no grove - a yashikirin is drawn on every farm "
            f"that can host one; only a paddy/neighbor/yard-shaded windward side may leave a farm grove-less",
        )
    return _kept(locals(), ('B', 'Hm', 'WF', 'Wm', 'avoid', 'c', 'clump_clear', 'corridors', 'crop_ol', 'dpl', 'fdx', 'fdy', 'hh_', 'min_clump', 'omitted', 'par', 'perp', 's'))


# NUCLEATED villages shelter behind a COMMUNAL fengshui WINDBREAK (风水林), NOT per-house groves: a
# dense grove belt on the high WINDWARD back edge (the winter-monsoon wall + sacred back-village
# grove), a smaller cluster at the low water-mouth entrance, and scattered bamboo/fruit copses. So a
# nucleated village is NOT required to grove every farm (groves_where_possible is skipped above for
# meta.nucleated); instead it MUST carry the village windbreak, on the windward side, off the paddies.
# WHY (the fengshui-forest research - ~2 groves/village, a ~1-2 ha back grove at ~3,400 stems/ha, a
# water-mouth cluster, kept off the crops and the road): settlements.md 'Village windbreak'.


def _seg_0285_082__vgroves(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.082 (vgroves) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vgroves = M.get("village_groves", [])
    return _kept(locals(), ('vgroves',))


def _seg_0285_083__village_windbreak_present(
    *,
    M: Any = _UNBOUND,
    c: Any = _UNBOUND,
    canopy: Any = _UNBOUND,
    ccx: Any = _UNBOUND,
    ccy: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fline: Any = _UNBOUND,
    fnear: Any = _UNBOUND,
    forest_shelters: Any = _UNBOUND,
    g: Any = _UNBOUND,
    h: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    i: Any = _UNBOUND,
    lee: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nestle_d: Any = _UNBOUND,
    roofs: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    subst_wb: Any = _UNBOUND,
    vgroves: Any = _UNBOUND,
    windbreaks: Any = _UNBOUND,
    windward: Any = _UNBOUND,
    wvx: Any = _UNBOUND,
    wvy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.083 (village_windbreak_embraces_cluster, village_windbreak_on_windward_side, village_windbreak_present, village_windbreak_scales_with_cluster) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city') and meta.get("nucleated") and len(houses) >= 10:
        windbreaks = [g for g in vgroves if g.get("role") == "windbreak"]
        check(
            "village_windbreak_present",
            bool(windbreaks),
            "a nucleated village shelters behind a COMMUNAL windbreak (a fengshui back-village grove), but "
            "no role='windbreak' village grove is present - add s.village_grove(..., role='windbreak') on the "
            "high windward edge",
        )
        # the belt backs the cluster on the WINDWARD/high side (default NW) - its centroid must lie
        # windward of the house-cluster centroid, so the wall faces the cold wind, not the sunny field side
        ccx = sum(h["x"] for h in houses) / len(houses)
        ccy = sum(h["y"] for h in houses) / len(houses)
        lee = [(round(g["x"]), round(g["y"])) for g in windbreaks if (g["x"] - ccx) * wvx + (g["y"] - ccy) * wvy <= 0]
        # THE BELT EMBRACES THE CLUSTER - the doctrine's "nestles against and embraces"
        # (GM 2026-07), automated via a form-aware ADJACENCY metric after the windward-
        # canopy-fraction metric failed calibration (approved Kikuta scores 4-18% on it):
        # at least one SUBSTANTIAL windbreak grove (>= 12 clumps) must stand within 150px
        # of a farmhouse. Far corner forest masses are welcome extras; a map with ONLY far
        # masses is decoration, not a wind wall. Calibrated 2026-07: approved maps nestle
        # at 37-131px (Kikuta's ribbon belt is the 131 outlier).
        # a map whose wood is a REAL FOREST (M["forest"], the edge-feature wood) can let that
        # forest BE the windbreak - the strongest wind wall of all - but ONLY where the wood
        # actually shelters THIS cluster: its tree line must come within the same NESTLE
        # distance of a farmhouse AND stand WINDWARD of the cluster centroid. A blanket
        # "has a forest -> exempt" is what let Moritono pass with an 11-clump belt while its
        # Shirin Forest sat 1,089 ft away on the LEE (E) side under an NW wind (GM 2026-07-25):
        # a wood downwind and a fifth of a mile off breaks no wind. Small forest_patches do NOT exempt.
        fline = M.get("forest") or []
        fnear = min(((seg_dist(h["x"], h["y"], fline[i], fline[i + 1]), fline[i]) for h in houses for i in range(len(fline) - 1)), default=None)
        forest_shelters = fnear is not None and fnear[0] <= 150 and (fnear[1][0] - ccx) * wvx + (fnear[1][1] - ccy) * wvy > 0
        subst_wb = [] if forest_shelters else [g for g in windbreaks if len(g.get("clumps", [])) >= 12]
        nestle_d = min((min(math.hypot(c[0] - h["x"], c[1] - h["y"]) for c in g["clumps"] for h in houses) for g in subst_wb), default=None)
        check(
            "village_windbreak_embraces_cluster",
            forest_shelters or (bool(subst_wb) and nestle_d is not None and nestle_d <= 150),
            f"no substantial windbreak belt (>= 12 clumps) nestles against the farm cluster (nearest {None if nestle_d is None else round(nestle_d)}px; want <= 150) - "
            f"the back-village grove EMBRACES the houses' windward fringe; far corner masses alone are decoration",
        )
        check(
            "village_windbreak_on_windward_side",
            not lee,
            f"the village windbreak sits on the LEE/sunny side of the cluster, not the windward {windward}: "
            f"{lee[:2]} - the back-village grove shelters the high windward edge and leaves the sunny field side open",
        )
        # THE BELT SCALES WITH THE CLUSTER (GM 2026-07-25, after Moritono's belt read as a few
        # blobs behind 16 farmhouses). The >= 12-clump embrace test above is a FIXED floor, so a
        # belt sized for a 5-house corner passes unchanged behind a whole hamlet. Measure the
        # SHELTER the map actually draws - the windbreak's canopy disks plus any per-house
        # yashikirin footprints (a map may do both, e.g. Hikari-no-Sato) - against the ROOF area
        # it shelters. Both sides are px^2, so the ratio is scale-free (a 2 ft/px village draws
        # smaller roofs AND, per meta()'s village bscale exemption, larger clumps; the ratio is
        # unaffected). WHY this framing: the doctrine (settlements.md 'Village windbreak') wants
        # the belt to be the settlement's LARGEST vegetation feature, and the research figure -
        # a modest village back grove under 1 ha, ~1,800 sq ft per household - sits near ratio
        # ~1.3 at our house sizes. So 0.40 is a floor against absurdity, not a target: a wind
        # wall covering less than half the ground its own roofs do is decoration. Calibrated on
        # the pool 2026-07-25: approved maps run 0.45 (Hoshizora, a town whose farm zone is a
        # thin wedge) through 7.27 (Hikari-no-Sato); Moritono's belt scored 0.30.
        canopy = sum(len(g.get("clumps", [])) * math.pi * g.get("r", 14) ** 2 for g in windbreaks)
        canopy += sum(g.get("w", 0) * g.get("h", 0) for g in M.get("groves", []))
        roofs = sum(h.get("w", 0) * h.get("h", 0) for h in houses)
        check(
            "village_windbreak_scales_with_cluster",
            forest_shelters or canopy >= 0.40 * roofs,
            f"the windbreak is too small for the cluster it shelters: {round(canopy)}px^2 of canopy over "
            f"{len(houses)} farmhouses covering {round(roofs)}px^2 of roof (ratio {canopy / roofs if roofs else 0:.2f}; want >= 0.40) - "
            f"the back-village grove is the settlement's LARGEST vegetation feature, so deepen the belt "
            f"(more clump rows) or wrap it further around the windward faces",
        )
    return _kept(locals(), ('c', 'canopy', 'ccx', 'ccy', 'fline', 'fnear', 'forest_shelters', 'g', 'h', 'i', 'lee', 'nestle_d', 'roofs', 'subst_wb', 'windbreaks'))


# every village grove (of any role) is DRY woodland - no TREE may stand in a flooded paddy. Test the
# DRAWN CLUMPS, not the recorded bbox center (GM 2026-07-25, same correction commons_clear_of_paddies
# already took): a back-village belt is a long crescent hugging the field edge, so the center of the
# box around it can sit over the crop while every tree in it stands on dry ground - Ueda's 87-clump
# belt scored exactly that. Testing the clumps also gives the check MORE teeth, not less: it now
# measures the same thing the placement does (village_grove skips a clump landing in a field), so a
# gen whose engine-side field list is empty - the recurring trap - is caught here instead of hidden.
# A grove that records no clumps at all falls back to its center, for older maps; one that records
# neither (a bare poly, as some check fixtures carry) contributes no test point rather than raising.


def _seg_0285_084__c_1(*, c: Any = _UNBOUND, g: Any = _UNBOUND, scale: Any = _UNBOUND, vgroves: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.084 (c, g, vg_pts) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vg_pts = [c for g in vgroves for c in (g.get("clumps") or ([[g["x"], g["y"]]] if "x" in g and "y" in g else []))]
    return _kept(locals(), ('c', 'g', 'vg_pts'))


def _seg_0285_085__c_2(*, c: Any = _UNBOUND, fields_ol: Any = _UNBOUND, ol: Any = _UNBOUND, scale: Any = _UNBOUND, vg_pts: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.085 (c, ol, vg_in_paddy) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        vg_in_paddy = [(round(c[0]), round(c[1])) for c in vg_pts if any(point_in_poly(c[0], c[1], ol) for ol in fields_ol)]
    return _kept(locals(), ('c', 'ol', 'vg_in_paddy'))


def _seg_0285_086__village_groves_clear_of_paddies(*, check: Any = _UNBOUND, scale: Any = _UNBOUND, vg_in_paddy: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.086 (village_groves_clear_of_paddies) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "village_groves_clear_of_paddies",
            not vg_in_paddy,
            f"village grove tree(s) stand IN a flooded paddy: {vg_in_paddy[:3]} - the fengshui windbreak stands on dry ground at the cluster's back and entrance, never out in the paddy",
        )
    return _kept(locals(), ())


# A grove clump (a tree blob, radius r) may abut a farmstead - trees stand right up against a house
# wall - but it must NOT OVERLAP a building/yard/garden footprint (a tree drawn ON the roof reads
# wrong). Both the placement (the village_grove keep-out uses the clump's FULL radius) and this check
# enforce it. The nominal blob radius is the measure; canopy leaves spilling a few px onto the eaves
# are "adjacent," which is fine. Covers the whole homestead: house, threshing yard, kitchen garden,
# draft byre, farm shed. WHY (trees beside, not on, the buildings): settlements.md 'Village windbreak'.


def _seg_0285_087___clm(*, cx: Any = _UNBOUND, cy: Any = _UNBOUND, g: Any = _UNBOUND, scale: Any = _UNBOUND, vgroves: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.087 (_clm, cx, cy, g) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        _clm = [(cx, cy, g.get("r", 6)) for g in vgroves for cx, cy in g.get("clumps", [])]
    return _kept(locals(), ('_clm', 'cx', 'cy', 'g'))


def _seg_0285_088__on_struct(*, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.088 (on_struct) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        on_struct = []  # type: ignore[var-annotated]
    return _kept(locals(), ('on_struct',))


def _seg_0285_089__cx_3(
    *,
    M: Any = _UNBOUND,
    _clm: Any = _UNBOUND,
    cx: Any = _UNBOUND,
    cy: Any = _UNBOUND,
    k: Any = _UNBOUND,
    o: Any = _UNBOUND,
    on_struct: Any = _UNBOUND,
    r: Any = _UNBOUND,
    rect: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0285.089 (cx, cy, k, o) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        for k in ("houses", "threshing_yards", "gardens", "byres", "farm_sheds"):
            for o in M.get(k, []):
                rect = _struct_rect(o)
                for cx, cy, r in _clm:
                    if pt_to_rect(cx, cy, rect) < r - 1:  # real penetration (just-touching is allowed)
                        on_struct.append((k, round(o["x"]), round(o["y"])))
                        break
    return _kept(locals(), ('cx', 'cy', 'k', 'o', 'on_struct', 'r', 'rect'))


def _seg_0285_090__grove_clumps_clear_of_structures(*, check: Any = _UNBOUND, on_struct: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.090 (grove_clumps_clear_of_structures) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        check(
            "grove_clumps_clear_of_structures",
            not on_struct,
            f"{len(on_struct)} farmstead footprint(s) have a grove-clump tree drawn OVER them: {on_struct[:4]} - "
            f"a copse/windbreak clump may stand right beside a house but never ON it; widen the village_grove "
            f"keep-out to the clump's full radius so the blob settles into the open ground beside the buildings",
        )
    return _kept(locals(), ())


# FUEL-AND-FODDER COMMONS - the degraded open grazing/scrub on the far side, BEYOND the back-grove.
# South China's hills were stripped for fuel/timber over a millennium (open pine + grass + erosion),
# so past the protected grove is NON-ARABLE waste: coarse grass, brush, scraggly pines - a commons,
# not a field, and never the flooded paddy. The land toposequence is village -> back-grove -> fuel
# commons, so the commons sits on the WINDWARD/high side and FURTHER out than the windbreak. WHY (the
# denuded hills + back-slope waste; graves + dry hill-crops also live here): settlements.md 'Village windbreak'.
# Test the DRAWN OUTCOME, not the patch's bbox CENTER. `commons()` skips every paddy point when it
# scatters, so scrub can never actually be drawn on a flooded field - "is the center over water" was
# only ever a PROXY for that, and a wrong one: an INTERIOR fill (the patch that clothes the voids an
# irregular field leaves inside its own bbox) legitimately has its center on the crop while every
# glyph it draws falls in the voids around it. Scoring the center would fail a correct patch, which
# is the same bbox-stands-in-for-real-geometry mistake as the phantom field tail. What genuinely
# goes wrong is a patch placed where it can clothe NOTHING - it silently draws nothing at all - so
# that is what we test: sample each patch and require real open (non-crop) ground under it.


def _seg_0285_091__commons(*, M: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0285.091 (commons) - body verbatim from _seg_0285__wells_clear_of_shrine_and_torii (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'village', 'hamlet') and scale in ('town', 'village', 'hamlet', 'city'):
        commons = M.get("commons", [])
    return _kept(locals(), ('commons',))


def _seg_0598__nucleated_records_cluster_seeding(*, M: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 598 (settlement_records_cluster_seeding) - hand-added 2026-08-16 past the
    legacy range (see _seg_0595 in segments_08 for the numbering convention). New-style:
    writes=()."""
    # A KNOB THAT CAN SILENTLY NOT-RECORD IS THE "CHECK THAT NEVER RUNS" SHAPE (known-open
    # ledger 2026-08-16, Kashikawa: the front rows + lane frontage seated all 20 houses, the
    # cluster-seeds cloud never ran, and the rolled cluster_shape knob went unhonored with
    # no trace on the manifest - the twin-detector axis silently fell back to the bbox
    # aspect). The declaration-exists ratchet (settlement_declares_a_land_fall is the
    # model): a nucleated scripted map must record either the honored knob
    # (meta.cluster_shape, written by cluster_seeds when the cloud runs) or the seeding
    # mode that replaced it (meta.cluster_seeding, written by stage_homesteads).
    if M["meta"].get("generated_by") and M["meta"].get("nucleated"):
        _cs_ok = ("cluster_shape" in M["meta"]) or ("cluster_seeding" in M["meta"])
        check(
            "settlement_records_cluster_seeding",
            _cs_ok,
            "a nucleated scripted map records neither meta.cluster_shape (the cluster-seeds cloud ran and honored the knob) nor meta.cluster_seeding (the rows/frontage passes seated every house and the rolled shape went unhonored) - a rolled knob must leave a trace either way, or it can silently not-record with nothing warning; stage_homesteads records the seeding mode",
        )
    return _kept(locals(), ())
