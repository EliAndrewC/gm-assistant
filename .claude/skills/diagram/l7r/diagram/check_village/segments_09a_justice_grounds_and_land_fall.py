"""Gate segments (justice grounds and land fall; keys 0555_000-0561) - bodies verbatim, registry order preserved."""

import math
from collections.abc import Mapping
from typing import Any

from l7r.diagram.settlement import BOUNDARY_STONE_CLEAR_FT, EXECUTION_GROUND_DEAD_CLEAR_FT

from .common_01_geometry import _box_hits_poly, _struct_rect, edge_gap, point_in_poly, poly_dist, rect_corners, seg_dist, within_edge_gap
from .common_03_capacity import _UNBOUND, _kept, empty_street_runs


def _seg_0555_000__ln(*, M: Any = _UNBOUND, ln: Any = _UNBOUND, scale: Any = _UNBOUND, st: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0555.000 (ln, routes_j, st) - body verbatim from _seg_0555__punishment_spot_in_the_core (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        routes_j = ([M["road"]] if M.get("road") else []) + [st["pts"] for st in M.get("town_streets", [])] + ([M["lane"]] if M.get("lane") else []) + [ln["pts"] for ln in M.get("lanes", [])]
    return _kept(locals(), ('ln', 'routes_j', 'st'))


def _seg_0555_001___route_dist_j(*, k: Any = _UNBOUND, px: Any = _UNBOUND, py: Any = _UNBOUND, r: Any = _UNBOUND, routes_j: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0555.001 (_route_dist_j) - body verbatim from _seg_0555__punishment_spot_in_the_core (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):

        def _route_dist_j(px: float, py: float) -> float:
            return min(seg_dist(px, py, r[k], r[k + 1]) for r in routes_j for k in range(len(r) - 1))

    return _kept(locals(), ('_route_dist_j',))


def _seg_0555_002__hamlet_has_punishment_spot(*, check: Any = _UNBOUND, meta: Any = _UNBOUND, psp_j: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0555.002 (capital_has_punishment_spot, city_has_punishment_spot, hamlet_has_punishment_spot, town_has_punishment_spot, village_has_punishment_spot) - body verbatim from _seg_0555__punishment_spot_in_the_core (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and meta.get("punishment_spot", True):
        check(
            f"{scale}_has_punishment_spot",
            bool(psp_j),
            "a seat of justice keeps a public punishment ground - cangue frame, flogging post, kneeling stone (s.punishment_spot(...); meta(punishment_spot=False) to omit)",
        )
    return _kept(locals(), ())


def _seg_0555_003__hamlet_has_execution_ground(*, check: Any = _UNBOUND, exg_j: Any = _UNBOUND, meta: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0555.003 (capital_has_execution_ground, city_has_execution_ground, hamlet_has_execution_ground, town_has_execution_ground, village_has_execution_ground) - body verbatim from _seg_0555__punishment_spot_in_the_core (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and meta.get("execution_ground", True):
        check(
            f"{scale}_has_execution_ground",
            bool(exg_j),
            "a seat of justice keeps an execution ground outside the settlement (s.execution_ground(...) + s.boundary_marker(...); meta(execution_ground=False) to omit)",
        )
    return _kept(locals(), ())


def _seg_0555_004__h(
    *,
    _inwall_j: Any = _UNBOUND,
    dwell_j: Any = _UNBOUND,
    ftpx_j: Any = _UNBOUND,
    h: Any = _UNBOUND,
    near_lim_p: Any = _UNBOUND,
    p: Any = _UNBOUND,
    psp_j: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    wall_j: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0555.004 (h, near_lim_p, out_p, p) - body verbatim from _seg_0555__punishment_spot_in_the_core (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        if psp_j and wall_j:
            # IN THE CORE. Walled: inside the rampart. Unwalled: genuinely among the dwellings, not
            # merely on the map - a display nobody walks past is not a display.
            out_p = [(round(p["x"]), round(p["y"])) for p in psp_j if not _inwall_j(p["x"], p["y"])]
        else:
            near_lim_p = 400.0 / ftpx_j
            out_p = [(round(p["x"]), round(p["y"])) for p in psp_j if sum(1 for h in dwell_j if math.hypot(p["x"] - h["x"], p["y"] - h["y"]) < near_lim_p) < 5]
    return _kept(locals(), ('h', 'near_lim_p', 'out_p', 'p'))


def _seg_0555_005__punishment_spot_in_the_core(*, check: Any = _UNBOUND, out_p: Any = _UNBOUND, scale: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 0555.005 (punishment_spot_in_the_core) - body verbatim from _seg_0555__punishment_spot_in_the_core (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):
        check(
            "punishment_spot_in_the_core",
            not out_p,
            f"punishment ground(s) at {out_p} stand outside the built core - the cangue is displayed where the town passes it daily, at the market or the magistracy frontage",
        )
    return _kept(locals(), ())


def _seg_0555_006__punishment_spot_by_the_traffic(
    *,
    _route_dist_j: Any = _UNBOUND,
    check: Any = _UNBOUND,
    far_p: Any = _UNBOUND,
    ftpx_j: Any = _UNBOUND,
    lim_p: Any = _UNBOUND,
    p: Any = _UNBOUND,
    psp_j: Any = _UNBOUND,
    routes_j: Any = _UNBOUND,
    scale: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0555.006 (punishment_spot_by_the_traffic) - body verbatim from _seg_0555__punishment_spot_in_the_core (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city') and routes_j:
        lim_p = 60.0 / ftpx_j  # ~60 REAL feet, the notice board's traffic criterion - same reason
        far_p = [(round(p["x"]), round(p["y"])) for p in psp_j if _route_dist_j(p["x"], p["y"]) > lim_p]
        check(
            "punishment_spot_by_the_traffic",
            not far_p,
            f"punishment ground(s) at {far_p} stand more than ~60 real ft from every street - shaming is sited on foot traffic, not on administrative convenience",
        )
    return _kept(locals(), ('far_p', 'lim_p', 'p'))


def _seg_0555_007__execution_ground_outside_the_settlement(
    *,
    M: Any = _UNBOUND,
    _beyond_the_dwellings_j: Any = _UNBOUND,
    _inwall_j: Any = _UNBOUND,
    _nearest_dwelling_gap_j: Any = _UNBOUND,
    _off_the_way_out_j: Any = _UNBOUND,
    _outside_the_settlement_j: Any = _UNBOUND,
    _route_dist_j: Any = _UNBOUND,
    _settlement_edge_gap_j: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bad_out_j: Any = _UNBOUND,
    bcx_j: Any = _UNBOUND,
    bcy_j: Any = _UNBOUND,
    bms_j: Any = _UNBOUND,
    bur_j: Any = _UNBOUND,
    check: Any = _UNBOUND,
    core_j: Any = _UNBOUND,
    crowd_j: Any = _UNBOUND,
    d: Any = _UNBOUND,
    dead_j: Any = _UNBOUND,
    dwell_j: Any = _UNBOUND,
    e: Any = _UNBOUND,
    eg: Any = _UNBOUND,
    exg_j: Any = _UNBOUND,
    exits_j: Any = _UNBOUND,
    f: Any = _UNBOUND,
    far_e: Any = _UNBOUND,
    farm_j: Any = _UNBOUND,
    ftpx_j: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gx: Any = _UNBOUND,
    gy: Any = _UNBOUND,
    h: Any = _UNBOUND,
    lim_dead_j: Any = _UNBOUND,
    lim_gate_j: Any = _UNBOUND,
    lim_out_j: Any = _UNBOUND,
    lim_road_j: Any = _UNBOUND,
    on_farm_j: Any = _UNBOUND,
    out_bms_j: Any = _UNBOUND,
    p: Any = _UNBOUND,
    px: Any = _UNBOUND,
    py: Any = _UNBOUND,
    r: Any = _UNBOUND,
    routes_j: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    unmarked_j: Any = _UNBOUND,
    wall_j: Any = _UNBOUND,
    worst_j: Any = _UNBOUND,
    wrong_j: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 0555.007 (execution_ground_by_the_road, execution_ground_clear_of_the_dead, execution_ground_no_nearer_the_houses_than_its_stone, execution_ground_off_the_farmland, execution_ground_on_the_outcast_side, execution_ground_outside_the_settlement, execution_ground_past_the_boundary_marker) - body verbatim from _seg_0555__punishment_spot_in_the_core (feature 024 per-check split; guards re-evaluated in the body, see split_oversized.py)."""
    if scale in ('town', 'city'):  # noqa: SIM102 - comment bank under the guard; combining would orphan it (023 convention)
        if exg_j:
            core_j = (sum(h["x"] for h in dwell_j) / len(dwell_j), sum(h["y"] for h in dwell_j) / len(dwell_j)) if dwell_j else None
            # OUTSIDE THE SETTLEMENT. Death pollution keeps the ground beyond the rampart, and beyond
            # the dwellings when there is no rampart to measure from. 120 real ft is the project's
            # standing pollution separation (the cremation ground and tanning yard use it too).
            lim_out_j = 120.0 / ftpx_j

            def _beyond_the_dwellings_j(r: Mapping[str, Any]) -> bool:
                # FOOTPRINT, not center (GM, 2026-07-27). A 60x60 ft ground's corner reaches ~42 ft
                # past its center and a city's 100x60 one ~58, so the center-to-center form of this
                # rule delivered as little as half the clearance it promised. It takes the whole
                # RECORD rather than a point for exactly that reason - there is no way to ask this
                # question correctly from an (x, y).
                return not dwell_j or not any(within_edge_gap(r, h, lim_out_j) for h in dwell_j)

            def _nearest_dwelling_gap_j(r: Mapping[str, Any]) -> float:
                return min((edge_gap(r, h) for h in dwell_j), default=float("inf"))

            bad_out_j = [(round(e["x"]), round(e["y"])) for e in exg_j if _inwall_j(e["x"], e["y"]) or not _beyond_the_dwellings_j(e)]
            check(
                "execution_ground_outside_the_settlement",
                not bad_out_j,
                f"execution ground(s) at {bad_out_j} sit inside the settlement (in the walls, or within ~120 real ft of a dwelling) - kegare puts the ground past the built edge",
            )
            # ON THE WAY OUT. The ground exists to be SEEN by travelers arriving; a ground hidden in a
            # back field deters nobody, which is the whole reason it is sited where it is. The anchor
            # is the road WHERE THERE IS ONE - but a walled seat's drawn streets all stop at the
            # rampart, so for those the exit itself is the anchor: the gate is the road (Hirameki
            # draws no extramural road at all, and measuring only to its intramural streets made the
            # rule unsatisfiable rather than strict).
            # A drawn road is a LINE, so the ground must hug it: ~120 real ft, the same order as
            # Suzugamori sitting on the Tokaido. A gate is a POINT standing in for the road that
            # leaves it, and the ground sits some way DOWN that road rather than on its threshold -
            # Edo's grounds were miles out along their highways - so the gate anchor gets ~400 ft.
            # Measuring a gate at the road's tolerance made the rule unsatisfiable on Hirameki, whose
            # only anchors are gates because every street it draws stops at the rampart.
            exits_j = [(g[0], g[1]) for g in (M.get("gates") or [])] + ([(M["gate"][0], M["gate"][1])] if M.get("gate") else [])
            lim_road_j, lim_gate_j = 120.0 / ftpx_j, 400.0 / ftpx_j

            def _off_the_way_out_j(px: float, py: float) -> bool:
                # Shared by the ground and by its boundary stone - both are road furniture, so both
                # answer to the same band rather than to two magic numbers that could drift apart.
                if routes_j and _route_dist_j(px, py) <= lim_road_j:
                    return False
                return not any(math.hypot(px - gx, py - gy) <= lim_gate_j for gx, gy in exits_j)

            if routes_j or exits_j:
                far_e = [(round(e["x"]), round(e["y"])) for e in exg_j if _off_the_way_out_j(e["x"], e["y"])]
                check(
                    "execution_ground_by_the_road",
                    not far_e,
                    f"execution ground(s) at {far_e} stand more than ~120 real ft from every road and every gate - the posts are meant to be read by everyone leaving town",
                )
            if core_j and bms_j:
                # PAST THE BOUNDARY STONE. The marker must lie between the settlement and the ground:
                # nearer the core than the ground is, AND nearer the ground than the core is.
                # ...and the stone itself stands OUTSIDE the settlement it bounds AND ON THE WAY OUT.
                # A dosojin among the houses bounds nothing; one sitting in an open field off the
                # road bounds nothing either. Both would satisfy the between-ness arithmetic above
                # while asserting the opposite of what the stone means - `sae` blocks pollution at
                # the point the ROAD leaves clean ground, so the stone has to stand on that road,
                # past the last dwelling. "Outside" is the SAME predicate the ground answers to, for
                # the same kegare reason and off the same 120 ft separation: the stone is the line
                # the ground sits beyond, so a stone drawn inside the built edge would put that line
                # in the wrong place and quietly certify a ground that is too close in.
                # (The road half was found by eye on a rendered Nagahara, not by the gate:
                # between-ness alone had let the stone drift into a field southwest of the highway.
                # The built-edge half was found by eye on Ubame: its dosojin stood 91 real ft from
                # the nearest merchant house, in among the west-end frontage beside the punishment
                # ground and a wellhead, with a fully green gate - because "outside" was tested as
                # `not _inwall_j(...)` alone and Ubame is UNWALLED, where that returns False for
                # every point on the map. A wall-only test does not merely relax on an unwalled
                # map, it passes anything. GM, 2026-07-26.)
                def _outside_the_settlement_j(r: Mapping[str, Any]) -> bool:
                    # WHY THE STONE'S "OUTSIDE" IS NOT THE GROUND'S. A rampart IS the settlement's
                    # edge, so a stone beyond it is past the line by construction, and the roadside
                    # suburb that grows outside a town gate is legitimately close to it. The ground
                    # keeps the dwelling clause as well, because kegare is a separation from PEOPLE
                    # and does not care which side of the wall those people live on.
                    #
                    # AND THE UNWALLED FIGURE IS 60 FT, NOT THE GROUND'S 120 (corrected 2026-07-27).
                    # The first draft of this rule reused 120 "rather than invent a second number
                    # for the same phrase" - which was the wrong instinct, and the audit that found
                    # the center-distance defects is what exposed it. 120 ft is a POLLUTION
                    # separation: it exists to hold a polluting installation off housing. A dosojin
                    # pollutes nothing. It is a marker standing where the road leaves clean ground,
                    # and a real one stands at the village edge, not a bowshot beyond it. All it
                    # needs is to be clear of the built-up area rather than among it, which is the
                    # same "legible band of open ground" question the burakumin seam asks - hence
                    # the same 60 ft. Borrowing the bigger number also squeezed the stone between
                    # its own floor and the ground beyond it into a ~25 ft band on Hoshizora, which
                    # is the smell of a constraint doing a job that is not its own.
                    return not _inwall_j(r["x"], r["y"]) if wall_j else not any(within_edge_gap(r, h, BOUNDARY_STONE_CLEAR_FT / ftpx_j) for h in dwell_j)

                out_bms_j = [b for b in bms_j if _outside_the_settlement_j(b) and not _off_the_way_out_j(b["x"], b["y"])]
                unmarked_j = [
                    (round(e["x"]), round(e["y"]))
                    for e in exg_j
                    if not any(
                        math.hypot(b["x"] - core_j[0], b["y"] - core_j[1]) < math.hypot(e["x"] - core_j[0], e["y"] - core_j[1])
                        and math.hypot(b["x"] - e["x"], b["y"] - e["y"]) < math.hypot(e["x"] - core_j[0], e["y"] - core_j[1])
                        for b in out_bms_j
                    )
                ]
                check(
                    "execution_ground_past_the_boundary_marker",
                    not unmarked_j,
                    f"execution ground(s) at {unmarked_j} have no boundary stone between them and the settlement - the dosojin is what makes the ground 'outside', and sae means 'to block' (a stone inside the built edge, or off the road out, does not count as one)",
                )
            elif core_j:
                check(
                    "execution_ground_past_the_boundary_marker",
                    False,
                    "an execution ground needs a boundary stone (s.boundary_marker(...)) on the road between it and the settlement - the ritual boundary the ground sits beyond",
                )
            if bms_j and dwell_j:
                # ...AND THE STONE STANDS NEARER THE HOUSES THAN THE GROUND DOES (GM, 2026-07-27:
                # "I would have expected that the boundary stone would always be closer to the
                # town's edge than the execution ground itself. Was that not always the case?").
                # It was not. The between-ness test above is two distances to the core CENTROID -
                # the mean position of every dwelling - which orders the two features radially about
                # one point and says nothing about the built EDGE. A settlement is not a disc, so
                # the stone can be further out along the west road while the ground sits nearer a
                # different stretch of housing: Ubame's ground came within 124 ft of the laborers'
                # quarter while its stone stood 204 ft out, and 86 of 118 dwellings were nearer the
                # killing ground than the stone that supposedly bounded it. Tango (427 of 849) and
                # Minami had the same defect.
                #
                # THIS IS NOT A FOOTPRINT BUG AND FOOTPRINTS DO NOT FIX IT. The arithmetic was
                # sound; the geometry it stood for was not. An AGGREGATE (the centroid) was
                # standing in for a DISTRIBUTED thing (the built edge), and the cure is to measure
                # to the nearest dwelling - whatever direction it lies in - rather than to the
                # average of all of them. Kept as its own check rather than folded into the one
                # above so the two failures are told apart: "no stone bounds this ground" and "the
                # stone bounds it on paper only" want different fixes.
                # WHAT "THE TOWN'S EDGE" IS, MEASURED. The rampart where there is one; the nearest
                # dwelling where there is not - the same definition the "outside" test above uses,
                # for the same reason, and it matters here more than there. Measuring a walled
                # city to its nearest dwelling makes an ISOLATED FARMHOUSE in the hinterland stand
                # for the settlement: Tango's execution ground sits in the extramural fields, and
                # the closest house to it is a farmstead 132 ft to its EAST - further out than the
                # ground itself - so a nearest-dwelling reading called the ground "nearer the town"
                # than a stone that plainly stands between the city and it (161 ft from the wall
                # against the ground's 295). A scattered farmstead is not the built edge; the wall
                # is. Unwalled, the nearest dwelling is the only edge there is to measure to.
                def _settlement_edge_gap_j(r: Mapping[str, Any]) -> float:
                    if wall_j:
                        return min(poly_dist(px, py, wall_j) for px, py in rect_corners(_struct_rect(dict(r))))
                    return _nearest_dwelling_gap_j(r)  # type: ignore[no-any-return]

                worst_j = []
                for e in exg_j:
                    eg = _settlement_edge_gap_j(e)
                    if all(_settlement_edge_gap_j(b) > eg for b in bms_j):
                        worst_j.append((round(e["x"]), round(e["y"]), round(eg * ftpx_j), round(min(_settlement_edge_gap_j(b) for b in bms_j) * ftpx_j)))
                check(
                    "execution_ground_no_nearer_the_houses_than_its_stone",
                    not worst_j,
                    f"execution ground(s) (x, y, ground_gap_ft, stone_gap_ft) {worst_j} stand CLOSER to the settlement edge (the rampart, or the nearest dwelling where there is none) than the boundary stone that bounds them - "
                    f"then the ground lies inside the stone's line for those households, whatever the arithmetic about the town's middle says. Move the ground further out, "
                    f"or the stone nearer the built edge",
                )
            # CLEAR OF THE COMMUNITY'S DEAD. Two different kinds of death: the tended ancestral dead
            # and the disposed unmourned. The executed go in the pit AT the ground; they are never
            # carried to the parish burial ground, and the two must not read as one precinct.
            dead_j = (M.get("cemeteries") or []) + (M.get("cremation_grounds") or []) + (M.get("ossuaries") or []) + (M.get("mausoleums") or [])
            lim_dead_j = EXECUTION_GROUND_DEAD_CLEAR_FT / ftpx_j
            crowd_j = [(round(e["x"]), round(e["y"])) for e in exg_j if any(within_edge_gap(e, d, lim_dead_j) for d in dead_j)]
            check(
                "execution_ground_clear_of_the_dead",
                not crowd_j,
                f"execution ground(s) at {crowd_j} sit within ~{EXECUTION_GROUND_DEAD_CLEAR_FT:.0f} real ft of a burial ground, cremation ground, ossuary, or mausoleum - the executed are disposed of where they die, never among the community's dead",
            )
            # OFF THE FARMLAND. Waste ground: gravel bar, dry riverbed, sandy bluff. Nobody plants
            # where the Empire kills, and nobody kills on land that pays tax.
            farm_j = [f["outline"] for f in M.get("fields", []) if f.get("outline")] + [d["poly"] for d in M.get("dry_plots", []) if d.get("poly")]
            on_farm_j = [(round(e["x"]), round(e["y"])) for e in exg_j if any(_box_hits_poly((e["x"] - e["w"] / 2, e["y"] - e["h"] / 2, e["x"] + e["w"] / 2, e["y"] + e["h"] / 2), p) for p in farm_j)]
            check(
                "execution_ground_off_the_farmland",
                not on_farm_j,
                f"execution ground(s) at {on_farm_j} overlap cultivated land - the ground is waste land, and taxed paddy is the last place it would go",
            )
            bur_j = [b for b in M.get("buildings", []) if b.get("kind") == "burakumin"]
            if core_j and bur_j:
                # ON THE OUTCAST SIDE. Pollution runs ONE way out of a settlement, and the burakumin
                # quarter already marks which way that is - the same people handle the fallen stock,
                # the tanning, the corpses, and (per l7r.md) every execution that is not a samurai's.
                # So the ground shares their side of the town.
                #
                # DIRECTION ONLY, deliberately (it began as "further out than the quarter as well",
                # which was unsatisfiable on a walled town: Hirameki's quarter is EXTRAMURAL at the SE
                # corner, so "further out" put the ground off the canvas). The claim the research
                # actually supports is directional - downwind, downstream, the outcast side - and
                # radius is an artifact of where the wall happens to be. The spec has this as a SHOULD
                # for the same reason: where it conflicts with the road placement, the road wins.
                bcx_j = sum(b["x"] for b in bur_j) / len(bur_j)
                bcy_j = sum(b["y"] for b in bur_j) / len(bur_j)
                wrong_j = [(round(e["x"]), round(e["y"])) for e in exg_j if (e["x"] - core_j[0]) * (bcx_j - core_j[0]) + (e["y"] - core_j[1]) * (bcy_j - core_j[1]) <= 0]
                check(
                    "execution_ground_on_the_outcast_side",
                    not wrong_j,
                    f"execution ground(s) at {wrong_j} lie on the opposite side of the settlement from the burakumin quarter - pollution runs ONE way out of a town, and the caste that performs the executions lives on that side",
                )
    return _kept(
        locals(),
        (
            '_beyond_the_dwellings_j',
            '_nearest_dwelling_gap_j',
            '_off_the_way_out_j',
            '_outside_the_settlement_j',
            '_settlement_edge_gap_j',
            'b',
            'bad_out_j',
            'bcx_j',
            'bcy_j',
            'bur_j',
            'core_j',
            'crowd_j',
            'd',
            'dead_j',
            'e',
            'eg',
            'exits_j',
            'f',
            'far_e',
            'farm_j',
            'g',
            'h',
            'lim_dead_j',
            'lim_gate_j',
            'lim_out_j',
            'lim_road_j',
            'on_farm_j',
            'out_bms_j',
            'p',
            'unmarked_j',
            'worst_j',
            'wrong_j',
        ),
    )


def _seg_0556__walled_town_has_wall(
    *,
    EMPTY_RUN: Any = _UNBOUND,
    M: Any = _UNBOUND,
    MAXGAP: Any = _UNBOUND,
    STEP: Any = _UNBOUND,
    a8: Any = _UNBOUND,
    amph_all2: Any = _UNBOUND,
    amph_raw2: Any = _UNBOUND,
    ax: Any = _UNBOUND,
    ay: Any = _UNBOUND,
    b: Any = _UNBOUND,
    bx: Any = _UNBOUND,
    by: Any = _UNBOUND,
    check: Any = _UNBOUND,
    cov: Any = _UNBOUND,
    d: Any = _UNBOUND,
    empty: Any = _UNBOUND,
    ff: Any = _UNBOUND,
    gate: Any = _UNBOUND,
    gate_t: Any = _UNBOUND,
    has_main: Any = _UNBOUND,
    hill: Any = _UNBOUND,
    houses: Any = _UNBOUND,
    hx: Any = _UNBOUND,
    hy: Any = _UNBOUND,
    i: Any = _UNBOUND,
    j: Any = _UNBOUND,
    k: Any = _UNBOUND,
    ki: Any = _UNBOUND,
    lens: Any = _UNBOUND,
    ln: Any = _UNBOUND,
    mains: Any = _UNBOUND,
    mean: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    mn: Any = _UNBOUND,
    occ: Any = _UNBOUND,
    occ_dist: Any = _UNBOUND,
    out_ls: Any = _UNBOUND,
    out_mm: Any = _UNBOUND,
    outside_biz: Any = _UNBOUND,
    ox: Any = _UNBOUND,
    oy: Any = _UNBOUND,
    p: Any = _UNBOUND,
    r: Any = _UNBOUND,
    run: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    st: Any = _UNBOUND,
    t: Any = _UNBOUND,
    w: Any = _UNBOUND,
    wallp_t: Any = _UNBOUND,
    worst: Any = _UNBOUND,
    x: Any = _UNBOUND,
    y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 556 (streets_have_buildings, wall_hugs_the_town, wall_sections_irregular, walled_town_commoners_inside_walls, walled_town_has_gate_market, walled_town_has_main_street, walled_town_has_wall) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "town" and meta.get("walled"):
        check("walled_town_has_wall", bool(M.get("wall")) and bool(M.get("gate")), "a walled town must have a wall and a gate")
        # COMMONERS SHELTER INSIDE THE RAMPART - the jokamachi doctrine every walled-town docstring
        # states, previously enforced by nothing (GM audit 2026-07; the town analog of
        # city_commoner_dwellings_inside_walls). Town exemptions differ from the city's: the
        # BURAKUMIN quarter is doctrinally OUTSIDE (segregated), and the guan-xiang gate market
        # keeps its merchant houses by the gate - so laborers/servants outside are hard-zero, and
        # a merchant dwelling outside must stand within ~260px of the gate.
        wallp_t = M.get("wall")
        gate_t = M.get("gate")
        if wallp_t and len(wallp_t) >= 3:
            out_ls = [(round(b["x"]), round(b["y"])) for b in M.get("buildings", []) if b.get("kind") in ("laborer", "laborer_large", "servant") and not point_in_poly(b["x"], b["y"], wallp_t)]
            out_mm = [
                (round(b["x"]), round(b["y"]))
                for b in M.get("buildings", [])
                if b.get("kind") in ("merchant", "merchant_house", "merchant_large")
                and not point_in_poly(b["x"], b["y"], wallp_t)
                and (not gate_t or math.hypot(b["x"] - gate_t[0], b["y"] - gate_t[1]) > 260)
            ]
            check(
                "walled_town_commoners_inside_walls",
                not out_ls and not out_mm,
                f"commoner dwelling(s) outside the rampart: laborers/servants {out_ls[:3]}, far-from-gate merchants {out_mm[:3]} - "
                f"a walled town's urban castes live INSIDE; only farmhouses, the segregated burakumin quarter, and the gate market belong outside",
            )

        w = M.get("wall") or []
        if len(w) >= 3:
            lens = [math.hypot(w[i + 1][0] - w[i][0], w[i + 1][1] - w[i][1]) for i in range(len(w) - 1)]
            # "irregular" = not a regular polygon: high spread in section lengths. A
            # coefficient of variation (stdev/mean) test, unlike a pairwise-equal test,
            # allows a wall to hug a feature with several short segments (the chrysanthemum
            # field) while still failing a lazy near-equal-sided wall.
            mean = sum(lens) / len(lens)
            cov = (sum((ln - mean) ** 2 for ln in lens) / len(lens)) ** 0.5 / mean if mean else 0
            check("wall_sections_irregular", len(lens) >= 5 and cov >= 0.25, f"wall has {len(lens)} sections, length CoV {cov:.2f} (need >= 5 sections and CoV >= 0.25 for an irregular rampart)")
        # the gate-to-yamen axis: a main street must run inward from the gate
        gate: Any = M.get("gate")  # type: ignore[no-redef]
        mains = [st for st in M.get("town_streets", []) if st.get("main")]
        has_main = bool(gate) and any(min(math.hypot(p[0] - gate[0], p[1] - gate[1]) for p in st["pts"]) < 75 for st in mains)
        check("walled_town_has_main_street", has_main, "a walled town needs a main street running inward from the gate (the gate-to-yamen axis)")

        # no "street to nowhere": a street exists to give access to the buildings along it,
        # and is paved/worn by the traffic to and from them - so no long INSIDE-the-walls
        # stretch may be empty of buildings. (Buildings off any street are fine; that's the
        # poor who can't afford street frontage.) The map edge / off-wall approach is exempt.
        empty = empty_street_runs(M, w)
        check(
            "streets_have_buildings",
            not empty,
            f"street(s) with a stretch inside the walls with no building FRONTING it (a street with no buildings would not exist - trim it or move buildings onto it): {empty}",
        )

        # a wall is expensive: it should HUG the built-up town, not enclose large empty
        # margins. Terrain can justify some slack (a wall climbs/skirts a hill rather than
        # leveling it), so the hill counts as filled "occupancy". Flag a long contiguous
        # stretch of wall whose inside is empty of any building, feature, or terrain - that
        # length of wall would not have been built; a tighter line costs less.
        if len(w) >= 3:
            occ = [(b["x"], b["y"]) for b in M.get("buildings", []) + houses if point_in_poly(b["x"], b["y"], w)]
            for ff in M.get("flower_fields", []):
                occ += [(p[0], p[1]) for p in ff["outline"][::3]]
            occ += [(r["x"], r["y"]) for r in M.get("religious", [])] + [(mn["x"], mn["y"]) for mn in M.get("manors", [])]
            amph_raw2 = M.get("theater_stage")
            amph_all2 = amph_raw2 if isinstance(amph_raw2, list) else ([amph_raw2] if amph_raw2 else [])
            occ += [(a8["x"], a8["y"]) for a8 in amph_all2]
            hill = M.get("hill")

            def occ_dist(x: float, y: float) -> float:
                d = min((math.hypot(ox - x, oy - y) for ox, oy in occ), default=1e9)
                if hill:
                    hx, hy, hrx, hry = hill
                    if ((x - hx) / hrx) ** 2 + ((y - hy) / hry) ** 2 <= 1.0:
                        return 0.0  # on the hill - terrain occupancy
                    d = min(d, min(math.hypot(hx + math.cos(math.tau * k / 48) * hrx - x, hy + math.sin(math.tau * k / 48) * hry - y) for k in range(48)))
                return d

            MAXGAP, EMPTY_RUN, STEP = 140, 280, 25
            run = worst = 0
            for ki in range(len(w) - 1):
                (ax, ay), (bx, by) = w[ki], w[ki + 1]
                for j in range(max(1, int(math.hypot(bx - ax, by - ay) // STEP))):
                    t = j / max(1, int(math.hypot(bx - ax, by - ay) // STEP))
                    if occ_dist(ax + (bx - ax) * t, ay + (by - ay) * t) > MAXGAP:
                        run += STEP
                        worst = max(worst, run)
                    else:
                        run = 0
            check("wall_hugs_the_town", worst <= EMPTY_RUN, f"~{worst:.0f}px of wall runs more than {MAXGAP}px from any building or terrain (it encloses empty space - draw a tighter wall)")

        # (RETIRED 2026-07-24: monastery_torii_scale_with_space - "roomy approach OWES the seven,
        # cramped corner keeps 1-2" - is superseded by the per-temple seeded ROLL, and it predated
        # the 1/3/7 TORII_WEIGHTS table besides (it still banned a count of 3, which the table
        # rolls at 60% for towns). Avenue completeness is now defined by the roll: shrine_hall
        # rolls each hall on the tier column, records the target, and torii_match_roll +
        # torii_count_canonical carry the teeth. Same precedent as torii_full_avenue_is_seven and
        # city_temple_torii_fill_approach.)

        # a walled town almost always accretes a small extramural MARKET (a Chinese guan-xiang)
        # just outside its gate. The WHY is traffic, not taxes (GM 2026-07-24, correcting the
        # rationale ported from the city tier): towns levy NO import tariffs (budgets.md puts
        # the whole tariff apparatus at provincial-city and capital gates only), and the county
        # magistrate governs the WHOLE county, so standing outside the gate crosses no tax or
        # regulatory line. The honest drivers are through-road travelers buying services without
        # detouring inside, the market-day chokepoint where the rural catchment trades, and late
        # arrivals at a gate shut for the night - so the market scales with GATE TRAFFIC, not
        # town population: typically ~4-8 permanent premises (floor >= 3), the small end of the
        # researched 10-40-per-trafficked-CITY-gate band. WHY: settlements.md "gate market" +
        # flophouse-research.md. Opt out with meta(gate_market=False) (a purely military fort,
        # or a depopulated / suppressed gate).
        if meta.get("gate_market", True):
            gate = M.get("gate")
            if gate and len(w) >= 3:
                outside_biz = [
                    b for b in M.get("buildings", []) if b.get("kind") in ("shop", "merchant") and not point_in_poly(b["x"], b["y"], w) and math.hypot(b["x"] - gate[0], b["y"] - gate[1]) <= 420
                ]
                check(
                    "walled_town_has_gate_market",
                    len(outside_biz) >= 3,
                    f"{len(outside_biz)} business(es) outside the gate - a walled town has a small gate market (guan-xiang) of a few shophouses unless meta(gate_market=False)",
                )
    return _kept(
        locals(),
        (
            'EMPTY_RUN',
            'MAXGAP',
            'STEP',
            'a8',
            'amph_all2',
            'amph_raw2',
            'ax',
            'ay',
            'b',
            'bx',
            'by',
            'cov',
            'empty',
            'ff',
            'gate',
            'gate_t',
            'has_main',
            'hill',
            'i',
            'j',
            'ki',
            'lens',
            'ln',
            'mains',
            'mean',
            'mn',
            'occ',
            'occ_dist',
            'out_ls',
            'out_mm',
            'outside_biz',
            'p',
            'r',
            'run',
            'st',
            't',
            'w',
            'wallp_t',
            'worst',
        ),
    )


# A MAP MUST DECLARE ITS LAND FALL (GM 2026-07-25). This closes the hole that let the whole
# problem happen: the drainage-slope block, `downhill_direction_valid` and `marsh_on_low_ground`
# are ALL gated on a fall being declared, and the code's own comment said "maps without the tag
# are exempt (slope unknown)" - so the two provincial cities, which declared none, silently
# skipped every one of those checks for months and nobody could tell from a green gate. Exempt
# is exactly what a map must not be. Either form counts: a map-level `meta(down_deg)`, or a
# per-field fall on every paddy (which is what a settlement ringed by farmland needs, since its
# fans drain several ways at once and no single bearing describes them).


def _seg_0557___lf_paddies(*, M: Any = _UNBOUND, f: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 557 (_lf_paddies, f) - body verbatim from the legacy gate() (feature 022)."""
    _lf_paddies = [f for f in M.get("fields") or [] if f.get("kind") == "paddy"]
    return _kept(locals(), ('_lf_paddies', 'f'))


def _seg_0558__settlement_declares_a_land_fall(
    *, M: Any = _UNBOUND, _lf_missing: Any = _UNBOUND, _lf_paddies: Any = _UNBOUND, check: Any = _UNBOUND, f: Any = _UNBOUND, meta: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 558 (settlement_declares_a_land_fall) - body verbatim from the legacy gate() (feature 022)."""
    if _lf_paddies or M.get("field_ditches"):
        _lf_missing = [f.get("name") for f in _lf_paddies if f.get("down_deg") is None]
        check(
            "settlement_declares_a_land_fall",
            meta.get("down_deg") is not None or (bool(_lf_paddies) and not _lf_missing),
            f"no land fall declared - give the map a meta(down_deg=...) or a per-field fall on every paddy "
            f"(paddies without one: {_lf_missing}). Every drainage-slope rule is gated on this, so a map that "
            f"declares nothing SKIPS them all and still shows a green gate - which is how both provincial "
            f"cities went unvalidated. Water flow (meta water_flow) is a separate declaration and does not substitute",
        )
    return _kept(locals(), ('_lf_missing', 'f'))


# WATER FLOW DIRECTION (GM 2026-07-24; the "why" lives in settlements.md "WATER FLOW").
# Every map declares a DRAINAGE BEARING - where this landscape sends its water - and every
# watercourse declares which way it runs. Before this, direction lived only in gen docstrings,
# so no check could read it and "downstream" was unverifiable; the tannery work is what
# exposed the gap. Angles use the same convention as down_deg (0 = east, 90 = south).


def _seg_0559___wf_courses() -> dict[str, Any]:
    """Gate segment 559 (_wf_courses) - body verbatim from the legacy gate() (feature 022)."""
    _wf_courses: list[tuple[str, dict[str, Any]]] = []
    return _kept(locals(), ('_wf_courses',))


def _seg_0560___wf_courses_1(*, M: Any = _UNBOUND, _wf_courses: Any = _UNBOUND, _wf_key: Any = _UNBOUND, o: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 560 (_wf_courses, _wf_key, o) - body verbatim from the legacy gate() (feature 022)."""
    for _wf_key in ("streams", "canals"):
        _wf_courses += [(_wf_key, o) for o in (M.get(_wf_key) or [])]
    return _kept(locals(), ('_wf_courses', '_wf_key', 'o'))


def _seg_0561__water_flow_declared(
    *,
    M: Any = _UNBOUND,
    _mf: Any = _UNBOUND,
    _wf: Any = _UNBOUND,
    _wf_against: Any = _UNBOUND,
    _wf_courses: Any = _UNBOUND,
    _wf_dd: Any = _UNBOUND,
    _wf_off: Any = _UNBOUND,
    _wf_undeclared: Any = _UNBOUND,
    _wfd: Any = _UNBOUND,
    _wfk: Any = _UNBOUND,
    _wfo: Any = _UNBOUND,
    _wfv: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i: Any = _UNBOUND,
    kk: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    o: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 561 (moat_declares_circulation, water_flow_consistent_with_slope, water_flow_declared, watercourses_declare_flow, watercourses_flow_downstream) - body verbatim from the legacy gate() (feature 022)."""
    if _wf_courses or M.get("moat"):
        _wf = meta.get("water_flow")
        check(
            "water_flow_declared",
            _wf is not None,
            "no meta(water_flow=...) - every map with water declares the DRAINAGE BEARING (where the "
            "landscape sends its water, 0 = east / 90 = south). It is settled BEFORE the map is drawn, "
            "because it decides which end of the settlement is downstream and therefore where the "
            "polluting trades, the burakumin quarter and the drains can go",
        )
        _wf_dd = meta.get("down_deg")
        if _wf is not None and _wf_dd is not None:
            _wf_off = abs((float(_wf) - float(_wf_dd) + 180) % 360 - 180)
            # STRICTLY under 90: water cannot run uphill. It may run very NEARLY along the contour -
            # that is what an artificial contour canal IS (aligned near-parallel to the contours,
            # deviating only enough to keep a working gradient) - so a large divergence is realistic
            # and only a NET UPHILL component is impossible. Widest in this pool: 60 deg.
            check(
                "water_flow_consistent_with_slope",
                _wf_off < 90,
                f"water_flow {_wf} deg runs {_wf_off:.0f} deg off the land's fall (down_deg {_wf_dd}) - at 90 deg or "
                f"more the water would have a NET UPHILL component, which gravity does not allow. Divergences "
                f"approaching 90 are fine and expected (a valley floor runs across the valley sides' fall; a contour "
                f"canal is built almost parallel to the contours) - it is crossing 90 that is impossible",
            )
        # "level" IS a declaration - a navigable canal has no drainage bearing by nature, not by omission
        _wf_undeclared = [f"{kk}[{i}]" for i, (kk, o) in enumerate(_wf_courses) if o.get("flow_deg") is None and o.get("flow") != "level"]
        check(
            "watercourses_declare_flow",
            not _wf_undeclared,
            f"watercourse(s) with no flow direction: {_wf_undeclared} - every stream/river/canal records which way "
            f"its water runs (s.stream/river/canal flow=, polyline authored UPSTREAM-FIRST by convention, "
            f"flow='reverse' for one stored the other way round)",
        )
        if _wf is not None:
            _wf_against = []
            for _wfk, _wfo in _wf_courses:
                _wfd = _wfo.get("flow_deg")
                if _wfd is None:
                    continue
                _wfv = abs((float(_wfd) - float(_wf) + 180) % 360 - 180)
                if _wfv >= 90:
                    _wf_against.append((_wfk, round(float(_wfd)), round(_wfv)))
            check(
                "watercourses_flow_downstream",
                not _wf_against,
                f"watercourse(s) running AGAINST the map's drainage bearing (course, flow_deg, divergence): {_wf_against} "
                f"- with water_flow {_wf} deg, a course 90 deg or more off it is carrying water back up the landscape. "
                f"Either its flow tag is reversed or the map's declared bearing is wrong. (A real cross-drainage "
                f"tributary would need the bearing revisited, not the check relaxed. Widest in this pool: 69 deg.)",
            )
        if M.get("moat"):
            _mf = M.get("moat_flow")
            check(
                "moat_declares_circulation",
                bool(_mf and _mf.get("inlet") and _mf.get("outlet")),
                "moat with no recorded circulation - a ring has no upstream end, so it records the point where its "
                "water ENTERS and the point where it LEAVES (s.moat derives these for an open river-cut moat; a "
                "closed moat's gen declares them with s.moat_flow). Without them a moated city has no downstream side",
            )
    return _kept(locals(), ('_mf', '_wf', '_wf_against', '_wf_dd', '_wf_off', '_wf_undeclared', '_wfd', '_wfk', '_wfo', '_wfv', 'i', 'kk', 'o'))
