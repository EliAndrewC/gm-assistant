"""Gate segments (margins lanes and wells; keys 0268-0285_005) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.settlement import label_aabb, label_quad, paddy_wet_rings, ring_touches, sat_overlap

from .common_01_geometry import (
    _LABEL_BY_KIND,
    _LABEL_GROUP,
    _LABEL_GROUPS,
    _box_hits_poly,
    kiln_quarters,
    point_in_poly,
    seg_dist,
    within_edge_gap,
)
from .common_02_overlap_policy import torii_halfbox
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
