"""Gate segments (kosatsuba and paddy basins; keys 0544-0601) - bodies verbatim, registry order preserved."""

import math
from typing import Any

from l7r.diagram.waterfields import dedup_ring, floor_overhang, pointed_ring

from .common_01_geometry import Poly, clip_to_convex, convex_hull, point_in_poly, poly_area, seg_closest, seg_dist
from .common_02_overlap_policy import GridIndex
from .common_03_capacity import _UNBOUND, DWELLING_KINDS, _kept

# A magistrate's manor sits at the EDGE of its settlement; its gate faces what it fronts - the
# town/hamlet it administers (the built-up centroid) OR the Imperial road it sits beside. There is
# no fixed default direction (it depends where the town is); SOUTH is the formal fallback. (At CITY
# scale M['manors'] are the scattered country estates, which face their own lanes - city_estate_gates_vary.)


def _seg_0544__manor_gate_faces_town(
    *,
    GATE_OUT: Any = _UNBOUND,
    M: Any = _UNBOUND,
    ang: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bad_mg: Any = _UNBOUND,
    c: Any = _UNBOUND,
    check: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dirs: Any = _UNBOUND,
    dwell_all: Any = _UNBOUND,
    k: Any = _UNBOUND,
    mn: Any = _UNBOUND,
    mroad: Any = _UNBOUND,
    o: Any = _UNBOUND,
    ovec: Any = _UNBOUND,
    rl: Any = _UNBOUND,
    rp: Any = _UNBOUND,
    rvx: Any = _UNBOUND,
    rvy: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tl: Any = _UNBOUND,
    tvx: Any = _UNBOUND,
    tvy: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 544 (manor_gate_faces_town) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("hamlet", "town") and M.get("manors"):
        GATE_OUT = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
        dwell_all = M.get("houses", []) + M.get("buildings", [])
        mroad = M.get("road")
        bad_mg = []
        for mn in M.get("manors", []):
            o = GATE_OUT.get(mn.get("gate_dir"), (0, 0))
            ang = math.radians(mn.get("rot", 0))
            ovec = (o[0] * math.cos(ang) - o[1] * math.sin(ang), o[0] * math.sin(ang) + o[1] * math.cos(ang))
            dirs = []
            if dwell_all:
                tvx = sum(b["x"] for b in dwell_all) / len(dwell_all) - mn["x"]
                tvy = sum(b["y"] for b in dwell_all) / len(dwell_all) - mn["y"]
                tl = math.hypot(tvx, tvy) or 1
                dirs.append((tvx / tl, tvy / tl))
            if mroad:
                rp = min((seg_closest(mn["x"], mn["y"], mroad[k], mroad[k + 1]) for k in range(len(mroad) - 1)), key=lambda c: (c[0] - mn["x"]) ** 2 + (c[1] - mn["y"]) ** 2)
                rvx, rvy = rp[0] - mn["x"], rp[1] - mn["y"]
                rl = math.hypot(rvx, rvy) or 1
                dirs.append((rvx / rl, rvy / rl))
            if dirs and max(ovec[0] * d[0] + ovec[1] * d[1] for d in dirs) < 0.45:
                bad_mg.append(mn.get("gate_dir"))
        check(
            "manor_gate_faces_town",
            not bad_mg,
            f"a magistrate's manor gate {bad_mg} faces neither the town it administers nor the road it fronts - "
            f"it sits at the settlement's edge, so its gate should open toward the town/road (no fixed default; south is the formal fallback)",
        )
    return _kept(locals(), ('GATE_OUT', 'ang', 'b', 'bad_mg', 'd', 'dirs', 'dwell_all', 'k', 'mn', 'mroad', 'o', 'ovec', 'rl', 'rp', 'rvx', 'rvy', 'tl', 'tvx', 'tvy'))


def _seg_0545__walled_town_has_fire_tower(*, M: Any = _UNBOUND, check: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 545 (walled_town_has_fire_tower) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "town" and meta.get("walled") and meta.get("fire_tower", True):
        # WALLED towns only (GM 2026-07-24, REVERTING the 2026-07 audit widening to all towns).
        # The audit argued an unwalled seat's "packed road-front core burns just the same", but an
        # unwalled town is drawn at detached village grain (bscale 1.0, field gaps for natural
        # breaks) - not the contiguous row fabric the hinomi-yagura historically watched - and
        # real unwalled administrative seats (jin'ya/daikansho towns) kept fire BELLS, stored
        # water, and fireproof kura, not watch towers; the freestanding rural tower is a
        # Meiji-and-later institution. WHY: settlements.md "Fire towers". Opt out per-map with
        # meta(fire_tower=False).
        check("walled_town_has_fire_tower", len(M.get("fire_towers", [])) >= 1, "a walled town's dense wooden core needs a fire-watch tower (s.fire_tower(...); meta(fire_tower=False) to omit)")
    return _kept(locals(), ())


def _seg_0546__hamlet_has_kosatsuba(
    *,
    M: Any = _UNBOUND,
    URBAN: Any = _UNBOUND,
    b: Any = _UNBOUND,
    b_kb: Any = _UNBOUND,
    check: Any = _UNBOUND,
    devs_kb: Any = _UNBOUND,
    edgeon_kb: Any = _UNBOUND,
    face_deg_kb: Any = _UNBOUND,
    far_kb: Any = _UNBOUND,
    floor_kb: Any = _UNBOUND,
    g: Any = _UNBOUND,
    k: Any = _UNBOUND,
    kbs: Any = _UNBOUND,
    lim_gate_kb: Any = _UNBOUND,
    lim_kb: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    mains_kb: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    off_main_kb: Any = _UNBOUND,
    r: Any = _UNBOUND,
    routes_kb: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    uncovered_kb: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 546 (capital_has_kosatsuba, city_has_kosatsuba, city_kosatsuba_per_gate, hamlet_has_kosatsuba, kosatsuba_by_the_road, kosatsuba_faces_the_road, kosatsuba_on_a_main_way, town_has_kosatsuba, village_has_kosatsuba) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("town", "city", "village", "hamlet") and meta.get("kosatsuba", True):
        # THE OFFICIAL NOTICE BOARD (kosatsuba), default-on at EVERY settlement tier
        # (GM 2026-07-24, from the town deep audit; ported to cities, then to villages
        # and hamlets, the same day). Every Edo settlement down to the hamlet kept the
        # state's edict board - the ofuregaki circulars reached the peasantry through it,
        # via the headman, who was REQUIRED to be functionally literate (he received,
        # copied, and relayed the circulars); one reader per settlement makes the board
        # work, and officials also read notices aloud, so peasant literacy is no
        # objection. Siting was a TRAFFIC decision, not an administrative one: highway
        # frontage, main street by the gate, bridgehead, market corner, the village's
        # main lane - the state talking at everyone who passes (Edo's principal board
        # stood at Nihonbashi). A CITY posted MANY boards, so a city DRAWS the set - the
        # principal board at its central market node PLUS one per main-gate approach
        # corridor (floor = gates + 1; city_kosatsuba_per_gate covers the corridors) -
        # and LABELS only one, whichever board has room for the label (GM 2026-07-24:
        # the same one-label convention as the fire towers and gate markets; an
        # unlabeled board also fits the tight gate verges a labeled one cannot).
        # DISTINCT from the magistrate's manor-gate board (Mode A program, buildings.md):
        # that one posts the bench's OUTPUT (verdicts, bounties) for people who come TO
        # the court, while this one posts standing law - and the manor/yamen deliberately
        # sits away from the busy frontage, so the settlement board must never default
        # there. WHY: settlements.md "Notice board (kosatsuba)". Opt out for a
        # suppressed/backwater seat with meta(kosatsuba=False).
        kbs = M.get("kosatsuba") or []
        floor_kb = (len(M.get("gates") or []) + 1) if scale == "city" else 1
        check(
            f"{scale}_has_kosatsuba",
            len(kbs) >= floor_kb,
            f"a city posts the SET: {floor_kb} boards - the principal at the central market node + one per main gate (s.kosatsuba(...); meta(kosatsuba=False) to omit)"
            if URBAN
            else "the settlement posts the state's standing law on an official notice board (s.kosatsuba(...) or s.place_kosatsuba(); meta(kosatsuba=False) to omit)",
        )
        routes_kb = ([M["road"]] if M.get("road") else []) + [st["pts"] for st in M.get("town_streets", [])] + ([M["lane"]] if M.get("lane") else []) + [ln["pts"] for ln in M.get("lanes", [])]
        lim_kb = 60.0 / float(meta.get("ftpx") or 1)  # ~60 REAL feet at any scale
        if kbs and routes_kb:
            far_kb = [(round(b["x"]), round(b["y"])) for b in kbs if min(seg_dist(b["x"], b["y"], r[k], r[k + 1]) for r in routes_kb for k in range(len(r) - 1)) > lim_kb]
            check("kosatsuba_by_the_road", not far_kb, f"notice board(s) at {far_kb} stand more than ~60 real ft from every road/main street - a kosatsu is read where people pass")
            # ON A MAIN WAY, not merely ON A WAY (GM 2026-08-02, from Ubame: the board stood a
            # legal 49 ft off a side lane while the high street - the road, 23 structures on
            # its frontage - ran 200 ft away; "it should be along the main road, in order to
            # be more noticed"). The kosatsu is the state talking at everyone who passes, and
            # on a map with a way HIERARCHY "everyone" walks the main way: every `roads` entry
            # is a major road by construction (road() draws Imperial trunks and their like)
            # and a `main: True` town street is the gate-to-yamen avenue - so where a map
            # declares either, the board must stand in the siting band of one of THOSE, and a
            # side street or lane within 60 ft satisfies kosatsuba_by_the_road while still
            # burying the institution. Maps whose network is undifferentiated (village/hamlet
            # lane webs, towns with no flagged main street) declare no hierarchy to violate
            # and are exempt - there place_kosatsuba's busiest-node scoring stands in for
            # "main". DELIBERATELY narrower than the punishment ground's siting (GM
            # 2026-08-02: "other map features like punishment grounds don't always need to be
            # along a main road, but a notice board must be" - the ground is a display for
            # locals who already know where justice is done; the board must AMBUSH the eye).
            mains_kb = ([r["pts"] for r in M.get("roads") or []] or ([M["road"]] if M.get("road") else [])) + [st["pts"] for st in M.get("town_streets", []) if st.get("main")]
            if mains_kb:
                off_main_kb = [(round(b["x"]), round(b["y"])) for b in kbs if min(seg_dist(b["x"], b["y"], r[k], r[k + 1]) for r in mains_kb for k in range(len(r) - 1)) > lim_kb]
                check(
                    "kosatsuba_on_a_main_way",
                    not off_main_kb,
                    f"notice board(s) at {off_main_kb} stand off every MAIN way - the board is posted to be noticed, so it goes on the main street/road (a road, or a main: True town street), never a side street or lane (GM 2026-08-02)",
                )
            # ORIENTATION, the other half of siting (GM 2026-07-27, catching Nagahara's third
            # board). A kosatsu is a BROADSIDE signboard: a 7x3 ft face under a little roof,
            # read by someone walking past without leaving the road. Standing it PERPENDICULAR
            # to the road turns the face edge-on to everyone approaching, so the traffic the
            # siting check fought for sees the board's ~6 in of thickness - the institution
            # fails while both the presence and distance checks stay green. Historically the
            # boards stood square to the highway frontage (the post-town kosatsuba, Edo's
            # Nihonbashi high-board) for exactly that reason. The glyph's LONG axis (`rot`) is
            # the board's face, so the rule is: rot must run within FACE_DEG of some route
            # SEGMENT inside the siting band. Any segment in the band counts, not merely the
            # nearest - a board at a junction or on a bend legitimately faces one of the two
            # ways that meet there (Nagahara's north board fronts a cross street 19px off
            # while a perpendicular one passes 15px away; the road-bend boards sit 12-18deg
            # off their nearest segment). 30deg keeps ~87% of the face presented to traffic
            # and leaves ~12deg of headroom over the worst legitimate case in the pool.
            face_deg_kb = 30.0
            edgeon_kb = []
            for b_kb in kbs:
                devs_kb = [
                    abs((float(b_kb.get("rot") or 0.0) - math.degrees(math.atan2(r[k + 1][1] - r[k][1], r[k + 1][0] - r[k][0])) + 90) % 180 - 90)
                    for r in routes_kb
                    for k in range(len(r) - 1)
                    if seg_dist(b_kb["x"], b_kb["y"], r[k], r[k + 1]) <= lim_kb
                ]
                if devs_kb and min(devs_kb) > face_deg_kb:
                    edgeon_kb.append((round(b_kb["x"]), round(b_kb["y"]), round(min(devs_kb))))
            check(
                "kosatsuba_faces_the_road",
                not edgeon_kb,
                f"notice board(s) at {edgeon_kb} (x, y, degrees off) stand edge-on to the way they front - a kosatsu is a broadside signboard, so its long axis runs ALONG the road (rot = the road's bearing), never across it",
            )
        if URBAN and kbs and M.get("gates"):
            # every trafficked gate's approach corridor carries a board (~800 real ft of the
            # gate - the corridor, not the furnished throat itself)
            lim_gate_kb = 800.0 / float(meta.get("ftpx") or 1)
            uncovered_kb = [[round(g[0]), round(g[1])] for g in M["gates"] if min(math.hypot(b["x"] - g[0], b["y"] - g[1]) for b in kbs) > lim_gate_kb]
            check(
                "city_kosatsuba_per_gate",
                not uncovered_kb,
                f"main gate(s) at {uncovered_kb} have no notice board on their approach corridor - a city posted a board at every trafficked gate (draw them all, label ONE)",
            )
    return _kept(
        locals(),
        ('b', 'b_kb', 'devs_kb', 'edgeon_kb', 'face_deg_kb', 'far_kb', 'floor_kb', 'g', 'k', 'kbs', 'lim_gate_kb', 'lim_kb', 'ln', 'mains_kb', 'off_main_kb', 'r', 'routes_kb', 'st', 'uncovered_kb'),
    )


# ===== THE JUSTICE WORKS: the punishment ground (in town) and the execution ground (outside) =====
# Two separate institutions, used at wildly different frequencies and sited by OPPOSITE logics, so
# conflating them would be a modeling error. WHY (all of it): settlements.md "Punishment spot",
# "Execution ground", "Boundary marker". The short version: a county seat HAS an execution ground
# because the Chinese confirmation chain sends the sentence back down to be carried out where the
# crime happened (which is also why the canon county budget funds a jail but no execution line -
# the jail holds the condemned while the warrant travels); Japanese kegare then pushes the ground
# past the built edge. The punishment ground stays in the core because its governing variable is
# foot traffic - it is a DISPLAY, and the beating itself is a court act inside the magistracy.


def _seg_0547__psp_j(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 547 (psp_j) - body verbatim from the legacy gate() (feature 022)."""
    psp_j = M.get("punishment_spots") or []
    return _kept(locals(), ('psp_j',))


def _seg_0548__exg_j(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 548 (exg_j) - body verbatim from the legacy gate() (feature 022)."""
    exg_j = M.get("execution_grounds") or []
    return _kept(locals(), ('exg_j',))


def _seg_0549__bms_j(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 549 (bms_j) - body verbatim from the legacy gate() (feature 022)."""
    bms_j = M.get("boundary_markers") or []
    return _kept(locals(), ('bms_j',))


def _seg_0550__ftpx_j(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 550 (ftpx_j) - body verbatim from the legacy gate() (feature 022)."""
    ftpx_j = float(meta.get("ftpx") or 1)
    return _kept(locals(), ('ftpx_j',))


def _seg_0551__b_3(*, M: Any = _UNBOUND, b: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 551 (b, dwell_j) - body verbatim from the legacy gate() (feature 022)."""
    dwell_j = M.get("houses", []) + [b for b in M.get("buildings", []) if b.get("kind") in DWELLING_KINDS]
    return _kept(locals(), ('b', 'dwell_j'))


def _seg_0552__wall_j(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 552 (wall_j) - body verbatim from the legacy gate() (feature 022)."""
    wall_j: Poly = M.get("wall") or []
    return _kept(locals(), ('wall_j',))


def _seg_0553___inwall_j(*, px: Any = _UNBOUND, py: Any = _UNBOUND, wall_j: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 553 (_inwall_j) - body verbatim from the legacy gate() (feature 022)."""

    def _inwall_j(px: float, py: float) -> bool:
        return len(wall_j) >= 3 and point_in_poly(px, py, wall_j)

    return _kept(locals(), ('_inwall_j',))


def _seg_0554__punishment_spot_only_at_a_seat_of_justice(*, check: Any = _UNBOUND, exg_j: Any = _UNBOUND, psp_j: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 554 (execution_ground_only_at_a_seat_of_justice, punishment_spot_only_at_a_seat_of_justice) - body verbatim from the legacy gate() (feature 022)."""
    if scale in ("hamlet", "village"):
        # Village authority topped out at banishment, and capital sentences were confirmed far above
        # the county. A settlement with no magistrate's court has neither institution.
        check("punishment_spot_only_at_a_seat_of_justice", not psp_j, f"a {scale} has no magistrate and no court - the punishment ground belongs to a county seat and above")
        check("execution_ground_only_at_a_seat_of_justice", not exg_j, f"a {scale} has no magistrate and no court - the execution ground belongs to a county seat and above")
    return _kept(locals(), ())


def _seg_0600__comb_floor_ends_at_the_collector(*, M: Any = _UNBOUND, check: Any = _UNBOUND, fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 600 (comb_floor_ends_at_the_collector) - hand-added 2026-08-16 past the
    legacy range (see _seg_0595 for the numbering convention); registered beside it, whose
    `fields` binding it shares. New-style: temps stay function-local, writes=()."""
    # A COMB'S FLOOR ENDS WHERE ITS COMMAND AREA DOES (known-open ledger 2026-08-16,
    # Mizuguchi's SE wedge: the raw envelope closed from the collector's thin head across
    # ~350 ft of bare ground to the outer thread's tail, and the base floor read as a green
    # needle jutting past the drain). Ground down-fall of the collector - extended LEVEL
    # beyond its drawn ends, exactly as the wedge filler extends it - cannot drain and is
    # never planted, so floor there is dead ground wearing the field's color. The predicate
    # is `floor_overhang`, imported from the engine and NOT restated - the same call
    # `build_comb`'s envelope trim makes. Tolerance 16 px: the outline legitimately runs ON
    # the collector centerline (its low edge IS the drain polyline), so only a protrusion
    # well past the drawn water (max halfw 6 px) can fire. Comb fans only (`fork` marks
    # one): a polder's floor legitimately runs past its inner ring drain to the dike.
    if M["meta"].get("generated_by"):
        _fe_bad: list[tuple[int, int, int]] = []
        for _fe_fld in fields:
            if not _fe_fld.get("fork") or not _fe_fld.get("outline"):
                continue
            _fe_dd = float(_fe_fld.get("down_deg", M["meta"].get("down_deg", 90.0)))
            _fe_ol = [(float(v[0]), float(v[1])) for v in _fe_fld["outline"]]
            for _fe_fd in M.get("field_ditches", []):
                if _fe_fd.get("role") != "drain" or _fe_fd.get("field") != _fe_fld.get("name"):
                    continue
                _fe_pts = [(float(q[0]), float(q[1])) for q in _fe_fd.get("poly") or []]
                if len(_fe_pts) < 2:
                    continue
                for _fe_p, _fe_ov in zip(_fe_ol, floor_overhang(_fe_ol, _fe_pts, _fe_dd), strict=True):
                    if _fe_ov > 16.0:
                        _fe_bad.append((round(_fe_p[0]), round(_fe_p[1]), round(_fe_ov)))
        check(
            "comb_floor_ends_at_the_collector",
            not _fe_bad,
            f"{len(_fe_bad)} field-outline vertex/vertices reach past the (flat-extended) drain collector line, worst {max([_b[2] for _b in _fe_bad], default=0)} px, at {[list(_b[:2]) for _b in _fe_bad[:4]]} - floor past the collector is ground the fan cannot drain or plant, wearing the field's color (Mizuguchi's SE needle); build_comb trims the envelope to the collector line, so regenerate the map",
        )
    return _kept(locals(), ())


def _seg_0603__paddy_plot_seams_shared(*, M: Any = _UNBOUND, check: Any = _UNBOUND, fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 602 (paddy_plot_seams_shared) - hand-added 2026-08-17 past the legacy range
    (see _seg_0595 for the numbering convention). No `_PLACEMENTS` entry: it reads only `M`,
    `check` and `fields`, so the tail of the derived order is as good a seat as any and one
    fewer decision to maintain. New-style: temps stay function-local, writes=()."""
    # TWO ADJACENT BASINS SHARE ONE BUND (GM 2026-08-17, on Inashiro: "a tiny little standalone
    # rectangle of earthen walls is just smack dab in the middle of where the field should be ...
    # it should basically always be the case that two adjacent rice paddies share a single earthen
    # wall rather than two different earthen walls"). This is the paddy counterpart of
    # `dry_plot_seams_shared` and the same physical rule one crop over. An aze is a puddled-mud
    # ridge ~1-2 ft wide, re-plastered every spring (azenuri - research/fields.md): it IS the wall
    # between two basins. Nobody builds two of them with a strip of bare mud in between - the strip
    # would be the most valuable land on the map lying idle, it drains neither basin, and the
    # second ridge doubles the azenuri for nothing. Real paddy fabric is a single connected bund
    # network meeting at T-junctions; a free-standing four-sided ring inside it is a modern
    # land-consolidation read at best and a drawing error at worst.
    #
    # TWO FAULTS, one rule, both measured on the pre-fix pool (2026-08-17):
    #   SEAM   - a run of bund with another plot's bund a short way off across DRY floor: two walls
    #            where one belongs. Inashiro 52 plots, kashikawa 57, mizuguchi 64, sawada 81.
    #   NESTED - a whole bund ring drawn INSIDE a neighbouring basin, so it reads as a free-standing
    #            rectangle of wall in the middle of somebody's paddy while that basin's own wall
    #            still runs all the way round it. This was the GM's original report - six of them on
    #            Inashiro, 70-73% of each ring inside one carved basin and 0% of it shared with
    #            anybody. `_fill_wedges` allowed it deliberately ("the filler may lap up to ~12 real
    #            ft onto a neighbor ... the seam just reads as the bund between two plots") - true
    #            only for a hairline lap along a shared edge, false for every filler whose ring
    #            landed a plot-width in. NOTE that the four frozen pre-fix fixtures score 0 here:
    #            an unrelated engine change had already re-rolled those six rings away by the time
    #            the fixtures were cut, which is exactly why the rule is written down rather than
    #            trusted to stay gone. The clause's teeth are held by
    #            `test_paddy_seams_fires_on_a_bund_ring_drawn_inside_a_basin`.
    #
    # A SHALLOW LAP IS NOT A FAULT and this rule does not report one. A plot drawn over part of its
    # neighbour paints out the stretch of bund it covers, so the pair still reads as one shared
    # wall; on the fixed Inashiro the deepest such lap covers 41% of a ring and the map reads
    # clean. Only near-containment inverts that, which is why the second clause counts the share of
    # ONE ring lying inside ONE neighbour rather than measuring a depth.
    #
    # THE TOLERANCE IS NOT GUESSED. Sampling every plot boundary on the pre-fix Inashiro and
    # measuring the gap to the nearest OTHER plot gives 23,897 samples at exactly 0.0 px and a
    # thin smear above it - the carve's own quads share `edge()` outputs vertex for vertex, so a
    # correctly shared bund reads 0. Anything above the width of the drawn stroke is therefore a
    # real strip, not measurement noise. 3 ft = two AZE_FT strokes: two bunds that close draw as
    # one line. Above 24 ft the ground between them is not a doubled bund at all, it is bare
    # FLOOR, which is `paddy_fan_gapless`'s business - so this check deliberately stops there
    # rather than restating that rule at a different tolerance. 20 ft of run keeps a rounded
    # corner's few-pixel nub from firing.
    #
    # WATER IS THE ONE HONEST REASON FOR A GAP: the carve holds each bank's bund off the drawn
    # stroke on purpose (`paddy_bunds_clear_the_supply_channels` is the rule that puts it there),
    # so two basins parted by a delivery ditch are correct. The strip is judged at its MIDPOINT -
    # the sample itself sits on the bank by construction, so testing it would exempt every
    # canal-side bund on the map.
    if M["meta"].get("generated_by"):
        _ps_ftpx = float(M["meta"].get("ftpx", 1.0) or 1.0)
        _ps_share = 3.0 / _ps_ftpx  # two AZE_FT strokes: this close, the two bunds ARE one line
        _ps_max = 24.0 / _ps_ftpx  # wider than this is bare floor, not a doubled bund
        _ps_run = 20.0 / _ps_ftpx  # a shorter run is a rounded corner's nub
        _ps_seams: list[tuple[int, int, int]] = []
        _ps_laps: list[tuple[int, int, int]] = []
        for _ps_fld in fields:
            _ps_rings = [[(float(q[0]), float(q[1])) for q in _ps_r] for _ps_r in (_ps_fld.get("plot_rings") or []) if len(_ps_r) >= 3]
            if not _ps_rings:
                continue
            _ps_wat: list[tuple[Poly, float]] = []
            for _ps_fd in M.get("field_ditches", []):
                if _ps_fd.get("field") == _ps_fld.get("name"):
                    _ps_wp = [(float(q[0]), float(q[1])) for q in _ps_fd.get("poly") or []]
                    if len(_ps_wp) >= 2:
                        _ps_wat.append((_ps_wp, max(float(_ps_fd.get("w", 2.0)), float(_ps_fd.get("w_tail", _ps_fd.get("w", 2.0)))) / 2 + _ps_share))
            for _ps_ch in M.get("channels", []):
                _ps_wp = [(float(q[0]), float(q[1])) for q in _ps_ch.get("poly") or []]
                if len(_ps_wp) >= 2:
                    _ps_wat.append((_ps_wp, float(_ps_ch.get("w", 2.0)) / 2 + _ps_share))
            for _ps_dc in M.get("drawn_channels", []):
                _ps_wp = [(float(q[0]), float(q[1])) for q in _ps_dc.get("pts") or []]
                if len(_ps_wp) >= 2:
                    _ps_wat.append((_ps_wp, max(float(_ps_dc.get("w0", 2.0)), float(_ps_dc.get("w1", 2.0))) / 2 + _ps_share))
            _ps_pond = [(float(_ps_fp["x"]), float(_ps_fp["y"]), float(_ps_fp["rx"]) + _ps_share, float(_ps_fp["ry"]) + _ps_share) for _ps_fp in M.get("field_ponds", []) if "rx" in _ps_fp]
            # index the rings by the box they can reach across (prunes only, never decides)
            _ps_idx = GridIndex(64.0)
            _ps_box: list[tuple[float, float, float, float]] = []
            for _ps_i, _ps_ring in enumerate(_ps_rings):
                _ps_bb = (min(q[0] for q in _ps_ring) - _ps_max, min(q[1] for q in _ps_ring) - _ps_max, max(q[0] for q in _ps_ring) + _ps_max, max(q[1] for q in _ps_ring) + _ps_max)
                _ps_box.append(_ps_bb)
                _ps_idx.add(_ps_bb[0], _ps_bb[1], _ps_bb[2], _ps_bb[3], _ps_i)
            for _ps_i, _ps_ring in enumerate(_ps_rings):
                _ps_len = _ps_best = 0.0
                _ps_spot = (0.0, 0.0)
                _ps_host: dict[int, int] = {}  # samples of THIS ring sitting inside each neighbour
                _ps_touch = 0  # ...and samples of it lying ON some neighbour's wall (a shared aze)
                _ps_tot = 0
                for _ps_e in range(len(_ps_ring)):
                    _ps_a, _ps_b = _ps_ring[_ps_e], _ps_ring[(_ps_e + 1) % len(_ps_ring)]
                    _ps_el = math.hypot(_ps_b[0] - _ps_a[0], _ps_b[1] - _ps_a[1])
                    _ps_n = max(1, int(_ps_el / 3.0))
                    for _ps_k in range(_ps_n):
                        _ps_t = _ps_k / _ps_n
                        _ps_x = _ps_a[0] + _ps_t * (_ps_b[0] - _ps_a[0])
                        _ps_y = _ps_a[1] + _ps_t * (_ps_b[1] - _ps_a[1])
                        _ps_tot += 1
                        _ps_gap, _ps_in, _ps_near, _ps_on = _ps_max + 1.0, 0.0, -1, False
                        for _ps_j in _ps_idx.near(_ps_x, _ps_y):
                            if _ps_j == _ps_i or not (_ps_box[_ps_j][0] <= _ps_x <= _ps_box[_ps_j][2] and _ps_box[_ps_j][1] <= _ps_y <= _ps_box[_ps_j][3]):
                                continue
                            _ps_o = _ps_rings[_ps_j]
                            # distance to the neighbour's BOUNDARY either way - `poly_dist` returns
                            # 0 for an interior point, which is exactly the depth this needs
                            _ps_d = min(seg_dist(_ps_x, _ps_y, _ps_o[_ps_m], _ps_o[(_ps_m + 1) % len(_ps_o)]) for _ps_m in range(len(_ps_o)))
                            _ps_on = _ps_on or _ps_d <= _ps_share
                            if point_in_poly(_ps_x, _ps_y, _ps_o):
                                _ps_in = max(_ps_in, _ps_d)  # depth INSIDE the neighbour's basin
                                _ps_gap = 0.0
                                if _ps_d > _ps_share:
                                    _ps_host[_ps_j] = _ps_host.get(_ps_j, 0) + 1
                            elif _ps_d < _ps_gap:
                                _ps_gap, _ps_near = _ps_d, _ps_j
                        _ps_touch += _ps_on
                        if _ps_in <= _ps_share and _ps_share < _ps_gap <= _ps_max and _ps_near >= 0:
                            _ps_o = _ps_rings[_ps_near]
                            _ps_cx = _ps_cy = 0.0
                            _ps_cd = _ps_max * 4 + 1.0
                            for _ps_m in range(len(_ps_o)):
                                _ps_qx, _ps_qy = seg_closest(_ps_x, _ps_y, _ps_o[_ps_m], _ps_o[(_ps_m + 1) % len(_ps_o)])
                                if math.hypot(_ps_qx - _ps_x, _ps_qy - _ps_y) < _ps_cd:
                                    _ps_cd, _ps_cx, _ps_cy = math.hypot(_ps_qx - _ps_x, _ps_qy - _ps_y), _ps_qx, _ps_qy
                            # FACING, not merely near: at a T-junction the far end of a bund runs
                            # AWAY from the neighbour it corners on, so its nearest-neighbour
                            # distance grows along the edge with nothing wrong. A doubled bund is
                            # two roughly PARALLEL walls, so the crossing to the neighbour is near
                            # NORMAL to this edge; 0.5 admits anything within 60 deg of normal.
                            if _ps_cd > 1e-9 and _ps_el > 1e-9 and abs((_ps_cx - _ps_x) * (_ps_b[0] - _ps_a[0]) + (_ps_cy - _ps_y) * (_ps_b[1] - _ps_a[1])) / (_ps_cd * _ps_el) > 0.5:
                                _ps_len = 0.0
                                continue
                            _ps_mx, _ps_my = (_ps_x + _ps_cx) / 2, (_ps_y + _ps_cy) / 2
                            # AND THE STRIP MUST BE BARE. A doubled bund is two walls with unplanted
                            # ground between them; where the ground between belongs to a basin there
                            # is no second wall to remove. This is not pedantry - the fan toe carries
                            # long re-entrant closing-rank plots, and a sample on such a plot's own
                            # boundary can have a far-off neighbour across its OWN basin. Testing the
                            # midpoint against every ring (this plot included) is what tells the two
                            # apart, and it is the same question `paddy_fan_gapless` asks of the fan.
                            if any(point_in_poly(_ps_mx, _ps_my, _ps_rings[_ps_c]) for _ps_c in _ps_idx.near(_ps_mx, _ps_my)):
                                _ps_len = 0.0
                                continue
                            _ps_wet = any(((_ps_mx - _ps_pe[0]) / _ps_pe[2]) ** 2 + ((_ps_my - _ps_pe[1]) / _ps_pe[3]) ** 2 <= 1.0 for _ps_pe in _ps_pond)
                            for _ps_wq, _ps_hw in _ps_wat:
                                if _ps_wet:
                                    break
                                _ps_wet = any(seg_dist(_ps_mx, _ps_my, _ps_wq[_ps_s], _ps_wq[_ps_s + 1]) < _ps_hw for _ps_s in range(len(_ps_wq) - 1))
                            if not _ps_wet:
                                _ps_len += _ps_el / _ps_n
                                if _ps_len > _ps_best:
                                    _ps_best, _ps_spot = _ps_len, (_ps_x, _ps_y)
                                continue
                        _ps_len = 0.0
                if _ps_best >= _ps_run:
                    _ps_seams.append((round(_ps_spot[0]), round(_ps_spot[1]), round(_ps_best)))
                # NESTED, not merely lapping. A plot drawn OVER part of its neighbour paints out
                # the stretch of bund it covers, so the pair still reads as one shared wall wherever
                # the lap runs along their common edge - measured on the fixed Inashiro, the deepest
                # such lap covers 41% of a ring and the map reads clean. What does NOT is a ring
                # sitting INSIDE a basin: the host's own wall is still drawn all the way round it,
                # so the reader sees a second, free-standing rectangle of wall in the middle of the
                # paddy - the GM's report exactly.
                #
                # TWO CONDITIONS, because the depth alone does not separate them. A ring that is
                # 60% inside a neighbour and 40% welded to the basins around it is an odd-shaped
                # parcel, not a floating box; a 24-seed cohort produced two of those and they read
                # fine. What makes the box a box is that it shares NO wall with anybody - so the
                # second condition is that almost none of the ring lies ON another plot's bund.
                # (The pre-fix Inashiro fillers: 70-73% inside, and 0% shared.) Stating both is
                # what let the depth stay at a level the real defect clears rather than a threshold
                # tuned until this pool happened to pass.
                if _ps_tot and _ps_host and max(_ps_host.values()) >= 0.6 * _ps_tot and _ps_touch < 0.25 * _ps_tot:
                    _ps_laps.append(
                        (round(sum(_ps_q[0] for _ps_q in _ps_ring) / len(_ps_ring)), round(sum(_ps_q[1] for _ps_q in _ps_ring) / len(_ps_ring)), round(100 * max(_ps_host.values()) / _ps_tot))
                    )
        check(
            "paddy_plot_seams_shared",
            not _ps_seams and not _ps_laps,
            f"{len(_ps_seams)} paddy plot(s) run a bund alongside a neighbour's across dry floor {[list(_ps_s) for _ps_s in _ps_seams[:4]]} (x, y, run px) and {len(_ps_laps)} draw their whole bund ring inside a neighbouring basin {[list(_ps_l) for _ps_l in _ps_laps[:4]]} (x, y, % of the ring inside it) - two adjacent basins share ONE aze, so a plot's boundary either coincides with its neighbour's, abuts water, or is the edge of the planted block; the wedge filler must fit each bare pocket to the bunds that already bound it instead of seating a shrunken rectangle inside it",
        )
    return _kept(locals(), ())


def _seg_0604__paddy_plots_are_workable_basins(*, M: Any = _UNBOUND, check: Any = _UNBOUND, fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 604 (paddy_plots_are_workable_basins) - hand-added 2026-08-17 past the legacy
    range (see _seg_0595 for the numbering convention). No `_PLACEMENTS` entry: it reads only `M`,
    `check` and `fields`, so the tail of the derived order is as good a seat as any."""
    # A PADDY BASIN CANNOT TAPER TO A POINT (GM ruling 2026-08-17, on the fan-toe SUNBURST that
    # future-work.md had been carrying as an open question: "I would like for us to be rendering
    # things that are realistic ... if this is a thing that needs to be fixed, then I would like it
    # to be fixed"). At two places on Inashiro eight to ten bunds 130-254 ft long converge on a
    # ~10 ft stretch of the collector bank at apex angles of 7.5 / 9.5 / 9.8 / 10.6 / 13.5 / 14.3
    # deg, and it is the one place the paddy fabric still reads machine-drawn.
    #
    # THE SHAPE IS REAL; THE ANGLES ARE NOT - and the distinction is the whole rule. A cascade fan
    # genuinely does narrow to its outfall, so radial convergence is authentic and is NOT what this
    # fires on. Narrowness is authentic too: the strips at Shiroyone Senmaida and in the Philippine
    # Cordilleras really are a few feet wide, so this is deliberately NOT a minimum-width rule.
    # What no real basin does is taper to ZERO. A paddy is a LEVEL, BUNDED, PUDDLED unit holding
    # standing water at an even depth; a 7.5 deg wedge is 5 ft wide 40 ft back from its point and
    # 2.6 ft at 20 ft, while an aze is ~1.5 ft of puddled mud (AZE_FT) on EACH side - so the last
    # yards of it are two bunds with no floor between them. That cannot be leveled, cannot hold a
    # depth, and cannot be transplanted. Real fan and terrace systems truncate the point instead:
    # the toe ends in a headland strip along the collector, or the odd corner is left unpaddied.
    # At 25 deg the same wedge is 17 ft wide 40 ft back, which is a workable bunded strip - that is
    # where the line sits and why.
    #
    # ONE PREDICATE, THE POOL'S OWN CALIBRATION, NO THIRD MAGIC NUMBER. `pointed_ring` already
    # answers "does this ring taper to a point", and both its thresholds were MEASURED across the
    # pool for the flooded-tint question (seam wedges 7-23 deg, honest hem strips 45+). This rule
    # reuses both ends rather than inventing its own: the carve TRUNCATES at 25 deg, this gate
    # fires at 15, so a borderline ring the carve leaves standing cannot false-fire the check -
    # the same placer-stricter-than-gate discipline as the supply-bank margins.
    #
    # `dedup_ring` FIRST, and it is not cosmetic. The envelope trim deposits near-duplicate
    # vertices (feature: `dedup_ring`'s own docstring), and the resulting micro-zigzag both hides
    # real apexes and invents fake ones - measured pool-wide, deduping moves Inashiro from 8
    # rings under 15 deg to 17. The raw ring is simply the wrong thing to measure, and this is the
    # same call the carve's own demotion makes.
    if M["meta"].get("generated_by"):
        _wb_bad: list[tuple[int, int]] = []
        for _wb_fld in fields:
            for _wb_r in _wb_fld.get("plot_rings") or []:
                _wb_ring = dedup_ring([(float(_wb_p[0]), float(_wb_p[1])) for _wb_p in _wb_r], 1.0)
                if len(_wb_ring) >= 3 and pointed_ring(_wb_ring, 15.0):
                    _wb_bad.append((round(sum(_wb_q[0] for _wb_q in _wb_ring) / len(_wb_ring)), round(sum(_wb_q[1] for _wb_q in _wb_ring) / len(_wb_ring))))
        check(
            "paddy_plots_are_workable_basins",
            not _wb_bad,
            f"{len(_wb_bad)} paddy plot(s) taper to a needle apex (interior angle < 15 deg) at {_wb_bad[:4]} - a paddy is a level bunded basin, and the last yards of a wedge that acute carry an aze on each side with no floor between them, so it can be neither leveled nor transplanted; a real fan toe ends in a headland or leaves the odd corner unpaddied rather than drawing the needle, so the plot must be DROPPED by the toe pass or ABSORBED into the basin beside it (pointed_ring at _TOE_MIN_APEX / _WELD_MIN_APEX) - no code truncates a corner, so do not go looking for it",
        )
    return _kept(locals(), ())


def _seg_0605__paddy_plot_rings_overcount_stays_marginal(*, M: Any = _UNBOUND, check: Any = _UNBOUND, fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 605 (paddy_plot_rings_overcount_stays_marginal) - hand-added 2026-08-17 past the
    legacy range (see _seg_0595 for the numbering convention). No `_PLACEMENTS` entry: it reads only
    `M`, `check` and `fields`. New-style: temps stay function-local, writes=()."""
    # `plot_rings` IS A PAINT-ORDER STACK, NOT A PARTITION - and this rule is what keeps that
    # ACCEPTED limitation from drifting into a lie (GM ruling 2026-08-17; the decision, the two
    # priced alternatives and why each was declined are in future-work.md, "`plot_rings` is a
    # paint-order STACK"). Each paddy is one <polygon> carrying fill AND stroke, emitted in index
    # order, so a later basin paints out the stretch of bund it laps and the pair reads as the
    # single shared wall a real fan has. The record is therefore honest about the INK and is NOT a
    # partition: sum the ring areas and you count the lapped ground twice.
    #
    # THE RULE IS A CEILING ON THAT OVER-COUNT, not a ban on the lap. Nothing in the gate measures
    # acreage off these rings today, so the cost is latent - it lands on the first future rule that
    # does (a per-field yield, a basin-to-basin adjacency). What the ceiling buys is that an
    # acreage read off the UNDISSOLVED stack stays wrong by less than one significant figure, which
    # is what makes comb.py's "dissolve before you measure" note a small documented approximation
    # rather than a trap.
    #
    # MEASURED, 2026-08-17, over the four scripted hamlets and a 48-seed cohort: sawada 0.53%,
    # kashikawa 0.54%, inashiro 0.79%, mizuguchi 1.06%; cohort median ~0.9%, and the tail runs
    # 1.49 / 1.51 / 1.57 / 2.49% (seed 24). `close_seams` halved the double-count as a side effect
    # (8,583 -> 4,445 sq ft on Inashiro), so the fabric is moving the right way on its own. 4.0% is
    # ~1.6x the worst live map and would fire on a doubling of it.
    #
    # WHY IT IS NOT TIGHTER, since the obvious question is why the ceiling does not fire on the
    # pre-`close_seams` Inashiro frozen in pool/regressions/. That manifest scores 2.58% against a
    # live worst of 2.49% - the two populations OVERLAP, so a map-wide lap fraction cannot separate
    # that defect from ordinary fabric, and a ceiling tuned to catch it would fail a cohort seed
    # that passes today. The defect it looks like is `paddy_plot_seams_shared`'s business (a whole
    # ring drawn inside a neighbour), and that rule does discriminate it. So this one is a DRIFT
    # ceiling, and its teeth are the synthetic break in
    # `test_paddy_ring_overcount_fires_when_a_ring_is_painted_over_its_neighbour` rather than a
    # frozen fixture - the honest home for a rule whose defect has never yet been shipped.
    #
    # THE MEASUREMENT IS AN UPPER BOUND, deliberately. Each pair is clipped against the NEIGHBOUR's
    # convex hull (`clip_to_convex`), which over-states a concave neighbour's share, and every
    # pairwise lap is summed, which double-counts ground three rings share - both errors push the
    # figure UP, so passing this ceiling is a real verdict while a marginal failure may be
    # generous. That buys a hand-rolled measurement: the true figure is a polygon UNION, and
    # shapely is an engine dependency (`waterfields/seams.py`) that the gate has never carried.
    # The drain hem is excluded - it is recorded separately and does not paint over the plots.
    if M["meta"].get("generated_by"):
        _pr_ceiling = 4.0  # percent of the recorded fabric; see the calibration above
        _pr_tot, _pr_lap = 0.0, 0.0
        _pr_worst: list[tuple[int, int, int]] = []
        for _pr_fld in fields:
            _pr_rings = [[(float(_pr_q[0]), float(_pr_q[1])) for _pr_q in _pr_r] for _pr_r in (_pr_fld.get("plot_rings") or []) if len(_pr_r) >= 3]
            if not _pr_rings:
                continue
            _pr_box, _pr_hull = [], []
            _pr_idx = GridIndex(64.0)
            for _pr_i, _pr_ring in enumerate(_pr_rings):
                _pr_tot += poly_area(_pr_ring)
                _pr_bb = (min(_pr_q[0] for _pr_q in _pr_ring), min(_pr_q[1] for _pr_q in _pr_ring), max(_pr_q[0] for _pr_q in _pr_ring), max(_pr_q[1] for _pr_q in _pr_ring))
                _pr_box.append(_pr_bb)
                _pr_hull.append(convex_hull(_pr_ring))
                _pr_idx.add(_pr_bb[0], _pr_bb[1], _pr_bb[2], _pr_bb[3], _pr_i)
            for _pr_i, _pr_ring in enumerate(_pr_rings):
                for _pr_j in _pr_idx.near_rect(_pr_box[_pr_i][0], _pr_box[_pr_i][1], _pr_box[_pr_i][2], _pr_box[_pr_i][3]):
                    if _pr_j <= _pr_i:
                        continue  # each pair once (the index reports both directions)
                    _pr_a = poly_area(clip_to_convex(_pr_ring, _pr_hull[_pr_j]))
                    if _pr_a > 0:
                        _pr_lap += _pr_a
                        _pr_worst.append((round(sum(_pr_q[0] for _pr_q in _pr_ring) / len(_pr_ring)), round(sum(_pr_q[1] for _pr_q in _pr_ring) / len(_pr_ring)), round(_pr_a)))
        if _pr_tot > 0:
            _pr_pct = 100.0 * _pr_lap / _pr_tot
            _pr_worst.sort(key=lambda _pr_w: -_pr_w[2])
            check(
                "paddy_plot_rings_overcount_stays_marginal",
                _pr_pct <= _pr_ceiling,
                f"recorded plot rings lap by {_pr_pct:.2f}% of the fabric they describe (ceiling {_pr_ceiling}%), worst pairs at {[list(_pr_w) for _pr_w in _pr_worst[:4]]} (x, y, lapped sq px) - `plot_rings` is a PAINT-ORDER STACK and a shallow lap is correct ink, but past this line the stack stops being a fair proxy for the fabric and any acreage summed off it is wrong by more than the figure's own precision; fix the CARVE that is laying whole basins over their neighbours (close_seams / the toe pass), not the record",
            )
    return _kept(locals(), ())


def _seg_0601__flooded_plots_read_as_basins(*, M: Any = _UNBOUND, check: Any = _UNBOUND, fields: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 601 (flooded_plots_read_as_basins) - hand-added 2026-08-16 past the legacy
    range (see _seg_0595 for the numbering convention). New-style: temps stay local, writes=()."""
    # A FLOODED PLOT IS A LEVELED BASIN, AND A BASIN IS NOT A NEEDLE (known-open ledger
    # 2026-08-16: at every fan seam the closing rank's converging sub-columns taper to sharp
    # apexes, and the ones carrying the FLOODED tint read as tiny triangular PONDS at fit zoom -
    # conspicuous on Sawada, whose brief is "no pond"). The predicate is `pointed_ring`,
    # imported from the engine and NOT restated - the same call the carve's demotion makes; the
    # carve demotes at 25 deg, this fires at 15 (only the unmistakable needles), so a borderline
    # plot the carve allows cannot false-fire. `flooded_plots` is the PICTURE record (which
    # plots are painted blue - `wet_plots` is the topography); manifests that record none
    # (pre-2026-08-16, or a fill path that never floods) skip, the plot_rings line the bead
    # checks hold.
    if M["meta"].get("generated_by") and M.get("flooded_plots"):
        _fb_rings = [_fb_r for _fb_fld in fields for _fb_r in (_fb_fld.get("plot_rings") or [])]
        _fb_cents = [(sum(_p[0] for _p in _fb_r) / len(_fb_r), sum(_p[1] for _p in _fb_r) / len(_fb_r)) for _fb_r in _fb_rings]
        _fb_bad: list[tuple[int, int]] = []
        for _fb_w in M["flooded_plots"]:
            _fb_wx, _fb_wy = float(_fb_w[0]), float(_fb_w[1])
            _fb_best, _fb_d = None, 3.0  # vertex-mean vs recorded centroid: a couple px of slack
            for _fb_i, (_fb_cx, _fb_cy) in enumerate(_fb_cents):
                _fb_dd = math.hypot(_fb_cx - _fb_wx, _fb_cy - _fb_wy)
                if _fb_dd < _fb_d:
                    _fb_best, _fb_d = _fb_i, _fb_dd
            if _fb_best is None:
                continue  # no ring near this centroid (a fill path with no recorded ring) - not judgeable
            if pointed_ring([(float(_p[0]), float(_p[1])) for _p in _fb_rings[_fb_best]], 15.0):
                _fb_bad.append((round(_fb_wx), round(_fb_wy)))
        check(
            "flooded_plots_read_as_basins",
            not _fb_bad,
            f"{len(_fb_bad)} FLOODED plot(s) taper to a needle apex (interior angle < 15 deg) at {_fb_bad[:4]} - a leveled flooded basin is bunded and near-rectangular, so a pointed blue sliver reads as a tiny pond hanging at the fan seam; the carve demotes pointed slivers to rice green (pointed_ring, 25 deg), so regenerate the map",
        )
    return _kept(locals(), ())
