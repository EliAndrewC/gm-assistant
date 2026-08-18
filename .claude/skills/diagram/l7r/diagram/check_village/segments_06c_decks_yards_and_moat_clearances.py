"""Gate segments (decks yards and moat clearances; keys 0387-0409) - bodies verbatim, registry order preserved."""

import collections
import math
from typing import Any

from .common_01_geometry import Pt, point_in_poly, seg_closest, seg_dist, segments_cross
from .common_03_capacity import _UNBOUND, _kept


def _seg_0387__ways_cross_water_on_a_deck(
    *,
    M: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    a9p: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    b9p: Any = _UNBOUND,
    check: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    j9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    l9: Any = _UNBOUND,
    r9: Any = _UNBOUND,
    s9: Any = _UNBOUND,
    t9: Any = _UNBOUND,
    wd_bad: Any = _UNBOUND,
    wd_bridges: Any = _UNBOUND,
    wd_kind: Any = _UNBOUND,
    wd_len: Any = _UNBOUND,
    wd_pts: Any = _UNBOUND,
    wd_w: Any = _UNBOUND,
    wd_waters: Any = _UNBOUND,
    wd_ways: Any = _UNBOUND,
    wp9: Any = _UNBOUND,
    ww9: Any = _UNBOUND,
    x9: Any = _UNBOUND,
    y9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 387 (ways_cross_water_on_a_deck) - body verbatim from the legacy gate() (feature 022)."""
    if wd_waters:
        wd_ways = ([("road", M["road"], float(M.get("road_width", 26)))] if M.get("road") else []) + [
            ("road", r9["pts"] if isinstance(r9, dict) else r9, float(r9.get("w", 20)) if isinstance(r9, dict) else 20.0) for r9 in M.get("roads", [])
        ]
        wd_ways += [("street", s9["pts"], float(s9.get("w", 18))) for s9 in M.get("town_streets", [])]
        wd_ways += [("alley", a9["pts"], float(a9.get("w", 10))) for a9 in M.get("alleys", [])]
        wd_ways += [("lane", l9["pts"] if isinstance(l9, dict) else l9, float(l9.get("w", 8)) if isinstance(l9, dict) else 8.0) for l9 in M.get("lanes", [])]
        if M.get("ring_road"):
            wd_ways.append(("ring road", list(M["ring_road"]) + [M["ring_road"][0]], float(M.get("ring_road_width", 15))))
        wd_bridges = M.get("bridges", [])
        wd_bad = []
        for wd_kind, wd_pts, wd_w in wd_ways:
            if len(wd_pts) < 2:
                continue
            for i9 in range(len(wd_pts) - 1):
                a9p, b9p = wd_pts[i9], wd_pts[i9 + 1]
                wd_len = math.hypot(b9p[0] - a9p[0], b9p[1] - a9p[1])
                for k9 in range(max(1, int(wd_len // 8)) + 1):
                    t9 = k9 / max(1, int(wd_len // 8))
                    x9, y9 = a9p[0] + (b9p[0] - a9p[0]) * t9, a9p[1] + (b9p[1] - a9p[1]) * t9
                    for wp9, ww9 in wd_waters:
                        if min(seg_dist(x9, y9, wp9[j9], wp9[j9 + 1]) for j9 in range(len(wp9) - 1)) < ww9 / 2 + wd_w / 2 - 3 and not any(
                            math.hypot(b9["x"] - x9, b9["y"] - y9) <= max(46.0, float(b9.get("span", 30))) for b9 in wd_bridges
                        ):
                            wd_bad.append((wd_kind, round(x9), round(y9)))
                        break
        check(
            "ways_cross_water_on_a_deck",
            not wd_bad,
            f"way(s) standing in water with no deck under them: {sorted(set(wd_bad))[:4]} - paving and water cannot share ground; "
            f"carry the way over on a bridge (s.bridges() after all ways and water, or a hand plank at the computed crossing), or route it clear of the bank",
        )
    return _kept(locals(), ('a9', 'a9p', 'b9', 'b9p', 'i9', 'j9', 'k9', 'l9', 'r9', 's9', 't9', 'wd_bad', 'wd_bridges', 'wd_kind', 'wd_len', 'wd_pts', 'wd_w', 'wd_ways', 'wp9', 'ww9', 'x9', 'y9'))


# A CAPITAL'S TRADES SCALE - IN FOUR DIFFERENT WAYS (GM question 2026-08-10, researched;
# the WHY, with sources, is in research/cities/capitals.md "Do a capital's trades and
# funerary program scale from a provincial city's?"). Nothing here is "same as a city":
#   LINEAR (multiply, same size): bathhouses at Edo's attested 1-per-2,000 sento ratio;
#     pawnshops at 1-per-400 (drawn representatively - 2-3 with their pledge-kura courts,
#     the rest implied in the shop rows); fire towers, linear in AREA on a fixed watch
#     radius (Kaifeng posted one every 300 paces from 1023).
#   SUBLINEAR (works consolidate): kilns cluster into a quarter beside each other, not
#     scattered; ONE cremation ground however big the city (Edo ran a million residents'
#     cremation through a handful of temple kasoba).
#   SUPERLINEAR (capital-only): permanent theater - Kaifeng's 50+ goulan against a
#     provincial town's touring stage - and the domain school.
#   FIXED (one per SEAT): the pauper's ossuary, by Song edict of 1104 (a louzeyuan in every
#     prefecture and county, regardless of size), and the primary mausoleum.
# INFERENCE, flagged: the kiln count of 2, the dyers'-row lot count, the oil-press band.


def _seg_0388__capital_trade_counts_scaled(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    k: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    scale: Any = _UNBOUND,
    tc_bad: Any = _UNBOUND,
    tc_bldg: Any = _UNBOUND,
    tc_have: Any = _UNBOUND,
    tc_pop: Any = _UNBOUND,
    tc_want: Any = _UNBOUND,
    v: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 388 (capital_trade_counts_scaled) - body verbatim from the legacy gate() (feature 022)."""
    if scale == "capital" and meta.get("population"):
        tc_pop = float(meta["population"])
        tc_bldg = collections.Counter(b.get("kind") for b in M.get("buildings", []))
        tc_have = {
            "bathhouses": len(M.get("bathhouses", [])) + tc_bldg.get("bathhouse", 0),
            "pawnshops": len(M.get("pawnshops", [])) + tc_bldg.get("pawnshop", 0),
            "breweries": len(M.get("breweries", [])) + tc_bldg.get("brewery", 0),
            "kilns": len(M.get("kilns", [])),
            "dye_yards": len(M.get("dye_yards", [])),
            "fire_towers": len(M.get("fire_towers", [])),
        }
        tc_want = {
            "bathhouses": (max(3, round(tc_pop / 2400)), "Edo's 523 sento per 1.1M - LINEAR, same size, more of them"),
            "pawnshops": (2, "Edo's 1-per-400 drawn representatively: 2-3 with pledge-kura courts, the rest implied in the rows"),
            "breweries": (2, "capacity is linear but brewing scaled by adding houses, not by doubling the hall (Takayama's 56 licensed brewers were mostly shopfronts)"),
            "kilns": (2, "a kiln is a QUARTER - the capital's second works stands beside the first, sharing the clay pit and fuel road (INFERENCE: the count of 2; the cluster form is attested)"),
            "dye_yards": (3, "a castle town lays out a Konya-machi: 3-5 contiguous dyer lots on one downstream bank, not one bigger yard (INFERENCE: the lot count)"),
            "fire_towers": (max(6, round(tc_pop / 1200)), "a fixed watch radius over a bigger built area (Kaifeng: a tower every 300 paces)"),
        }
        tc_bad = [f"{k}: {tc_have[k]} vs >= {v[0]} ({v[1]})" for k, v in tc_want.items() if tc_have[k] < v[0]]
        check(
            "capital_trade_counts_scaled",
            not tc_bad,
            f"capital trade counts below the researched floor: {tc_bad[:3]} - a capital is not a provincial city with a bigger wall; "
            f"see research/cities/capitals.md for which trades multiply, which consolidate, and which are capital-only",
        )
    return _kept(locals(), ('b', 'k', 'tc_bad', 'tc_bldg', 'tc_have', 'tc_pop', 'tc_want', 'v'))


# THE FRAME HUGS THE CONTENT (GM 2026-08-10: "it doesn't look like we're doing [cropping] on
# the south or east sides, especially the south"). A crop override outlives the feature it
# was added for - Shiro Daika carried south=240/east=700 from a layout three re-lays old -
# and dead margin reads as a map that forgot to finish. Each side of the view must have real
# DRAWN CONTENT within a reasonable band of the edge; linear features running off-map (the
# river, a road) do not count as content for this - they leave whether or not the frame follows.


def _seg_0389__fr_view(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 389 (fr_view) - body verbatim from the legacy gate() (feature 022)."""
    fr_view = meta.get("view")
    return _kept(locals(), ('fr_view',))


def _seg_0390__map_frame_hugs_its_content(
    *,
    M: Any = _UNBOUND,
    check: Any = _UNBOUND,
    fr_bad: Any = _UNBOUND,
    fr_band: Any = _UNBOUND,
    fr_h: Any = _UNBOUND,
    fr_hh: Any = _UNBOUND,
    fr_hw: Any = _UNBOUND,
    fr_k: Any = _UNBOUND,
    fr_pts: Any = _UNBOUND,
    fr_r: Any = _UNBOUND,
    fr_v: Any = _UNBOUND,
    fr_view: Any = _UNBOUND,
    fr_w: Any = _UNBOUND,
    fr_x: Any = _UNBOUND,
    fr_y: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    p: Any = _UNBOUND,
    q: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 390 (map_frame_hugs_its_content) - body verbatim from the legacy gate() (feature 022)."""
    if fr_view and len(fr_view) == 4:
        fr_x, fr_y, fr_w, fr_h = fr_view
        fr_band = 150.0 / float(meta.get("ftpx", 1) or 1)  # 150 real ft: the GM's ~100 ft target plus the crop margin's own slack (2026-08-10)
        fr_pts: list[tuple[float, float]] = []  # type: ignore[no-redef]
        for fr_k, fr_v in M.items():
            if fr_k in ("meta", "title", "scalebar", "districts") or not isinstance(fr_v, list):
                continue
            for fr_r in fr_v:
                if isinstance(fr_r, dict) and isinstance(fr_r.get("x"), (int, float)):
                    # the EXTENT, not the center: a kiln's yard reaches 20px past its record, and
                    # the crop frames boxes - measuring centers reads a tight frame as loose
                    fr_hw = float(fr_r.get("w", 0) or fr_r.get("r", 0) * 2 or 0) / 2
                    fr_hh = float(fr_r.get("h", 0) or fr_r.get("r", 0) * 2 or 0) / 2
                    fr_pts += [(fr_r["x"] - fr_hw, fr_r["y"] - fr_hh), (fr_r["x"] + fr_hw, fr_r["y"] + fr_hh)]
                elif fr_k == "labels" and isinstance(fr_r, (list, tuple)) and len(fr_r) >= 4:
                    # a CAPTION is drawn ink and the frame must contain it (labels_within_image),
                    # so a label box legitimately sets an edge - the crop's own box list includes it
                    fr_pts += [(float(fr_r[0]), float(fr_r[1])), (float(fr_r[2]), float(fr_r[3]))]
                elif fr_k in ("alleys", "town_streets", "torii") and isinstance(fr_r, dict) and fr_r.get("pts"):
                    # a drawn WAY inside the frame is content (its end is a real place); the
                    # river/road polylines are not - they leave the map whatever the frame does,
                    # and districts are declarations, not ink
                    fr_pts += [(q[0], q[1]) for q in fr_r["pts"] if fr_x <= q[0] <= fr_x + fr_w and fr_y <= q[1] <= fr_y + fr_h]
        if fr_pts:
            fr_bad = []
            if not any(p[1] > fr_y + fr_h - fr_band for p in fr_pts):
                fr_bad.append("south")
            if not any(p[1] < fr_y + fr_band for p in fr_pts):
                fr_bad.append("north")
            if not any(p[0] > fr_x + fr_w - fr_band for p in fr_pts):
                fr_bad.append("east")
            if not any(p[0] < fr_x + fr_band for p in fr_pts):
                fr_bad.append("west")
            check(
                "map_frame_hugs_its_content",
                not fr_bad,
                f"map frame carrying dead margin on the {fr_bad} side(s) - no drawn feature within 150 ft of the edge; "
                f"drop the stale per-side crop override (s.crop_city(south=..., east=...)) and let the frame follow the content",
            )
    return _kept(locals(), ('fr_bad', 'fr_band', 'fr_h', 'fr_hh', 'fr_hw', 'fr_k', 'fr_pts', 'fr_r', 'fr_v', 'fr_w', 'fr_x', 'fr_y', 'p', 'q'))


# NO DUNG AT A SAMURAI'S FRONT DOOR (GM 2026-08-10: "cattle yards should NOT go directly in
# front of the gates of samurai estates. No samurai wants literal piles of dung outside
# their front door. I'd expect that oxen yard to be next to the caravan inn anyway.")
# A stable/ox yard is a working animal ground - straw, dung, flies, noise - and the ONE
# place it may not stand is the approach a walled compound's gate opens onto. The rule
# measures to the GATE POINT (gate_dir names the side), not the compound's center, because
# the offense is the approach, not the neighborhood: a yard behind an estate's back wall
# is ordinary city ground. Yards belong with the traffic they serve - the caravan inn and
# its relay stables - which is where every other yard on this map already sits.


def _seg_0391__ay_bad() -> dict[str, Any]:
    """Gate segment 391 (ay_bad) - body verbatim from the legacy gate() (feature 022)."""
    ay_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('ay_bad',))


def _seg_0392__ay_reach(*, meta: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 392 (ay_reach) - body verbatim from the legacy gate() (feature 022)."""
    ay_reach = 240.0 / float(meta.get("ftpx", 1) or 1)  # 240 real ft of clear approach
    return _kept(locals(), ('ay_reach',))


def _seg_0393__ay_bad_1(
    *,
    M: Any = _UNBOUND,
    ay_bad: Any = _UNBOUND,
    ay_c: Any = _UNBOUND,
    ay_g: Any = _UNBOUND,
    ay_gd: Any = _UNBOUND,
    ay_h: Any = _UNBOUND,
    ay_key: Any = _UNBOUND,
    ay_r: Any = _UNBOUND,
    ay_reach: Any = _UNBOUND,
    ay_w: Any = _UNBOUND,
    ay_y: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 393 (ay_bad, ay_c, ay_g, ay_gd) - body verbatim from the legacy gate() (feature 022)."""
    for ay_c in M.get("manors", []) + M.get("merchant_estates", []):
        ay_gd = ay_c.get("gate_dir")
        if not ay_gd:
            continue
        ay_w, ay_h = ay_c.get("w", 0), ay_c.get("h", 0)
        ay_g = {
            "west": (ay_c["x"] - ay_w / 2, ay_c["y"]),
            "east": (ay_c["x"] + ay_w / 2, ay_c["y"]),
            "north": (ay_c["x"], ay_c["y"] - ay_h / 2),
            "south": (ay_c["x"], ay_c["y"] + ay_h / 2),
        }.get(ay_gd)
        if ay_g is None:
            continue
        for ay_key in ("stable_yards", "byres", "animal_grounds"):
            for ay_y in M.get(ay_key, []):  # every yard key holds records, never raw polygons
                ay_r = float(ay_y.get("r", 0) or max(ay_y.get("w", 0), ay_y.get("h", 0)) / 2)
                if math.hypot(ay_y["x"] - ay_g[0], ay_y["y"] - ay_g[1]) - ay_r < ay_reach:
                    ay_bad.append((ay_key, round(ay_y["x"]), round(ay_y["y"]), ay_c.get("label") or "a walled compound"))
    return _kept(locals(), ('ay_bad', 'ay_c', 'ay_g', 'ay_gd', 'ay_h', 'ay_key', 'ay_r', 'ay_w', 'ay_y'))


def _seg_0394__animal_yards_clear_of_compound_gates(*, ay_bad: Any = _UNBOUND, check: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 394 (animal_yards_clear_of_compound_gates) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "animal_yards_clear_of_compound_gates",
        not ay_bad,
        f"animal yard(s) standing on a walled compound's gate approach: {sorted(set(ay_bad))[:4]} - straw, dung and flies do not "
        f"belong at a samurai's front door; move the yard to the caravan inn and relay stables it serves, or behind the compound's back wall",
    )
    return _kept(locals(), ())


# EXTRAMURAL FEATURES STAY TETHERED TO THE CITY (GM 2026-08-10: "the kiln works is wayyyyy
# out in the middle of nowhere... the gate markets look pretty far from the actual gates").
# Everything outside a wall belongs to something: a gate's market strings along its
# approach road FROM the gate, the nuisance works sit on the near ground the city can still
# police and reach, and the wharf trades belong to the landing. So an outside feature must
# be within reach of a GATE, of the WHARF works, or of a road it stands on - a feature that
# is near none of the three is floating, whatever its bearing from the city.


def _seg_0395__extramural_features_tethered(
    *,
    M: Any = _UNBOUND,
    b: Any = _UNBOUND,
    check: Any = _UNBOUND,
    g: Any = _UNBOUND,
    gm_allow: Any = _UNBOUND,
    gm_bad: Any = _UNBOUND,
    gm_g: Any = _UNBOUND,
    gm_near: Any = _UNBOUND,
    gm_shops: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    j: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    r: Any = _UNBOUND,
    rp: Any = _UNBOUND,
    wx: Any = _UNBOUND,
    wy: Any = _UNBOUND,
    xm_bad: Any = _UNBOUND,
    xm_f: Any = _UNBOUND,
    xm_ftpx: Any = _UNBOUND,
    xm_gate_reach: Any = _UNBOUND,
    xm_key: Any = _UNBOUND,
    xm_road_reach: Any = _UNBOUND,
    xm_roads: Any = _UNBOUND,
    xm_wall: Any = _UNBOUND,
    xm_wharf: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 395 (extramural_features_tethered, gate_markets_start_at_their_gate) - body verbatim from the legacy gate() (feature 022)."""
    if len(M.get("wall") or []) >= 3 and M.get("gates"):
        xm_wall = M["wall"]
        xm_ftpx = float(meta.get("ftpx", 1) or 1)
        xm_gate_reach = 900.0 / xm_ftpx  # 900 real ft: the gate market's own strip
        xm_road_reach = 150.0 / xm_ftpx  # a works ON its haul road, not adrift beside it
        xm_wharf = [(j["x"], j["y"]) if isinstance(j, dict) else (j[0], j[1]) for j in M.get("jetties", [])]
        xm_wharf += [(g["x"], g["y"]) for g in M.get("granaries", []) if isinstance(g, dict) and "x" in g]
        xm_roads = ([M["road"]] if M.get("road") else []) + [r["pts"] if isinstance(r, dict) else r for r in M.get("roads", [])]
        xm_bad = []
        for xm_key in ("kilns", "dye_yards", "tanning_yards", "lumber_yards", "shops", "inns", "stables", "flophouses"):
            for xm_f in M.get(xm_key, []):
                if not isinstance(xm_f, dict) or "x" not in xm_f or point_in_poly(xm_f["x"], xm_f["y"], xm_wall):
                    continue
                if min(math.hypot(xm_f["x"] - g[0], xm_f["y"] - g[1]) for g in M["gates"]) <= xm_gate_reach:
                    continue
                if xm_wharf and min(math.hypot(xm_f["x"] - wx, xm_f["y"] - wy) for wx, wy in xm_wharf) <= 300:
                    continue
                if xm_roads and min(min(seg_dist(xm_f["x"], xm_f["y"], rp[i9], rp[i9 + 1]) for i9 in range(len(rp) - 1)) for rp in xm_roads if len(rp) >= 2) <= xm_road_reach:
                    continue
                # ...or simply CLOSE TO THE WALL it serves. A works on the near farm ground is
                # tethered by the city's own edge even with no road under it - which is where
                # every shipped map's nuisance works actually sits: 225-1,382 ft from the wall
                # across Tango, Minami, Nagahara and the capital (measured 2026-08-10). The kiln
                # that prompted this rule stood at 1,563 ft with nothing around it, so the band
                # is drawn from the attested spread rather than picked.
                if min(seg_dist(xm_f["x"], xm_f["y"], xm_wall[i9], xm_wall[(i9 + 1) % len(xm_wall)]) for i9 in range(len(xm_wall))) <= 1450.0 / xm_ftpx:
                    continue
                xm_bad.append((xm_key, round(xm_f["x"]), round(xm_f["y"])))
        check(
            "extramural_features_tethered",
            not xm_bad,
            f"outside feature(s) adrift - not within 900 ft of a gate, on a road, or at the wharf: {sorted(set(xm_bad))[:4]} - "
            f"every extramural feature belongs to something; pull it onto its approach road (a works hauls on the road it uses), "
            f"into the gate's market strip, or to the landing",
        )
        # ...and a GATE MARKET starts AT its gate. A market strip that begins hundreds of feet
        # down the road reads as an unrelated hamlet: the stalls crowd the gate mouth because
        # that is where the toll, the inspection and the traffic are.
        gm_bad = []
        for gm_g in M["gates"]:
            gm_shops = [
                b
                for b in M.get("buildings", []) + M.get("shops", [])
                if isinstance(b, dict) and b.get("kind") in ("shop", "merchant") and not point_in_poly(b["x"], b["y"], xm_wall) and math.hypot(b["x"] - gm_g[0], b["y"] - gm_g[1]) <= xm_gate_reach
            ]
            if len(gm_shops) >= 3:
                gm_near = min(math.hypot(b["x"] - gm_g[0], b["y"] - gm_g[1]) for b in gm_shops)
                # a MOAT pushes the head of the strip out by its own width plus the bridge's
                # landing - stalls cannot stand on the crossing - so the allowance grows by the
                # moat band where one runs past this gate (the capital's N gate, 2026-08-10)
                # THE POOL'S OWN SPREAD IS THE WHOLE ANSWER (GM 2026-08-10, twice): the nearest
                # stall sits 157-273 ft from the gate at Tango, Minami and Nagahara - and those
                # are walled, moated cities with the same gate program, bridge and guard works.
                # So the moat and the furniture are ALREADY inside that figure, and the first
                # cut's mistake was adding them again on top: a 260 ft blocked band plus a
                # 280 ft market allowance let the capital's markets start 540 ft out, which is
                # exactly the 300-ish feet the GM was still seeing. One flat band, no addition.
                gm_allow = 300.0 / xm_ftpx
                if gm_near > gm_allow:
                    gm_bad.append((round(gm_g[0]), round(gm_g[1]), round(gm_near)))
        check(
            "gate_markets_start_at_their_gate",
            not gm_bad,
            f"gate market(s) whose nearest stall is far down the road (gate x, y, px): {gm_bad[:4]} - a gate market crowds the "
            f"gate mouth where the toll and the traffic are, then strings outward; move the head of the strip up to the gate",
        )
    return _kept(
        locals(),
        (
            'b',
            'g',
            'gm_allow',
            'gm_bad',
            'gm_g',
            'gm_near',
            'gm_shops',
            'i9',
            'j',
            'r',
            'rp',
            'wx',
            'wy',
            'xm_bad',
            'xm_f',
            'xm_ftpx',
            'xm_gate_reach',
            'xm_key',
            'xm_road_reach',
            'xm_roads',
            'xm_wall',
            'xm_wharf',
        ),
    )


# PUBLIC WELLS DO NOT KNOT UP (GM 2026-08-10: "several places with 4-6 wells clustered
# right next to each other... not how wells are positioned on any other map"). A public
# well serves a neighborhood, so wellheads spread out - and the whole pool agrees: every
# settled map from hamlet to provincial city maxes at FOUR wells inside a 150 real-ft
# radius (measured across all 14, 2026-08-10), while the capital's density-chasing had
# piled up NINE. The failure mode is accretion - each new well is added to fix a local
# household count, none is added against the wells already there - so the rule is a
# neighborhood CAP, not a pairwise spacing floor (a tight PAIR at a big junction is fine).


def _seg_0396__w9(*, M: Any = _UNBOUND, w9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 396 (w9, wk_ws) - body verbatim from the legacy gate() (feature 022)."""
    wk_ws = [w9 for w9 in M.get("wells", []) if isinstance(w9, dict)]
    return _kept(locals(), ('w9', 'wk_ws'))


def _seg_0397__wells_not_clustered(
    *, check: Any = _UNBOUND, meta: Any = _UNBOUND, o9: Any = _UNBOUND, w9: Any = _UNBOUND, wk_bad: Any = _UNBOUND, wk_n: Any = _UNBOUND, wk_r: Any = _UNBOUND, wk_ws: Any = _UNBOUND
) -> dict[str, Any]:
    """Gate segment 397 (wells_not_clustered) - body verbatim from the legacy gate() (feature 022)."""
    if len(wk_ws) >= 5:
        wk_r = 150.0 / float(meta.get("ftpx", 1) or 1)
        wk_bad = []
        for w9 in wk_ws:
            wk_n = sum(1 for o9 in wk_ws if (w9["x"] - o9["x"]) ** 2 + (w9["y"] - o9["y"]) ** 2 <= wk_r * wk_r)
            if wk_n > 4:
                wk_bad.append((round(w9["x"]), round(w9["y"]), wk_n))
        check(
            "wells_not_clustered",
            not wk_bad,
            f"well knot(s) - more than 4 public wells inside a 150 ft radius (x, y, count): {sorted(set(wk_bad))[:4]} - a wellhead serves a NEIGHBORHOOD, so they spread; this is accretion from chasing a local household count. Widen the grid spacing over that quarter instead of stacking wells, and gate any top-up on there being no well already within the radius",
        )
    return _kept(locals(), ('o9', 'w9', 'wk_bad', 'wk_n', 'wk_r'))


# A WAY DOES NOT RUN INSIDE A ROAD'S BED (GM 2026-08-10: a service lane sat fully inside
# the Imperial road's kagi leg - two ways drawn where one exists on the ground). Sampled
# run-length of any lane/street/alley inside a road's half-width; short crossings pass.


def _seg_0398__r9_1(*, M: Any = _UNBOUND, r9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 398 (r9, rb_roads) - body verbatim from the legacy gate() (feature 022)."""
    rb_roads = ([{"pts": M["road"], "w": M.get("road_width", 26)}] if M.get("road") else []) + [r9 if isinstance(r9, dict) else {"pts": r9, "w": 20} for r9 in M.get("roads", [])]
    return _kept(locals(), ('r9', 'rb_roads'))


def _seg_0399__rb_bad() -> dict[str, Any]:
    """Gate segment 399 (rb_bad) - body verbatim from the legacy gate() (feature 022)."""
    rb_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('rb_bad',))


def _seg_0400__a9_1(
    *,
    M: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    i9: Any = _UNBOUND,
    inside9: Any = _UNBOUND,
    j9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    rb_bad: Any = _UNBOUND,
    rb_kind: Any = _UNBOUND,
    rb_list: Any = _UNBOUND,
    rb_pts: Any = _UNBOUND,
    rb_roads: Any = _UNBOUND,
    rb_run: Any = _UNBOUND,
    rb_w: Any = _UNBOUND,
    rp9: Any = _UNBOUND,
    seg_len9: Any = _UNBOUND,
    steps9: Any = _UNBOUND,
    t9: Any = _UNBOUND,
    x9: Any = _UNBOUND,
    y9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 400 (a9, b9, i9, inside9) - body verbatim from the legacy gate() (feature 022)."""
    for rb_kind, rb_list in (("street", M.get("town_streets", [])), ("alley", M.get("alleys", [])), ("lane", M.get("lanes", []))):
        for rb_w in rb_list:
            rb_pts = rb_w["pts"] if isinstance(rb_w, dict) else rb_w
            rb_run = 0.0
            for i9 in range(len(rb_pts) - 1):
                a9, b9 = rb_pts[i9], rb_pts[i9 + 1]
                seg_len9 = math.hypot(b9[0] - a9[0], b9[1] - a9[1])
                steps9 = max(1, int(seg_len9 // 15))
                for j9 in range(steps9 + 1):
                    t9 = j9 / steps9
                    x9, y9 = a9[0] + (b9[0] - a9[0]) * t9, a9[1] + (b9[1] - a9[1]) * t9
                    inside9 = any(min(seg_dist(x9, y9, rp9["pts"][k9], rp9["pts"][k9 + 1]) for k9 in range(len(rp9["pts"]) - 1)) < rp9["w"] / 2 for rp9 in rb_roads if len(rp9["pts"]) >= 2)
                    rb_run = rb_run + 15 if inside9 else 0.0
                    if rb_run > 45:
                        rb_bad.append((rb_kind, round(rb_pts[0][0]), round(rb_pts[0][1])))
                        break
                if rb_run > 45:
                    break
    return _kept(locals(), ('a9', 'b9', 'i9', 'inside9', 'j9', 'k9', 'rb_bad', 'rb_kind', 'rb_list', 'rb_pts', 'rb_run', 'rb_w', 'rp9', 'seg_len9', 'steps9', 't9', 'x9', 'y9'))


# (per-way: first offense reports, rest of the way skipped)


def _seg_0401__ways_not_inside_road_beds(*, check: Any = _UNBOUND, rb_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 401 (ways_not_inside_road_beds) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "ways_not_inside_road_beds",
        not rb_bad,
        f"way(s) running INSIDE a road's paved bed for 45+px: {sorted(set(rb_bad))[:4]} - two ways drawn where the ground has one; delete the duplicate (the road itself serves the frontage), or move the lane clear of the bed",
    )
    return _kept(locals(), ())


# A STREET REACHES THE NEIGHBOR IT POINTS AT (GM 2026-08-10: several street ends stopped
# a visible gap short of a crossing street - past the near-miss check's 30px cap but well
# inside "obviously meant to join"). An END whose direction of travel points (align > 0.6)
# at another street's bed within 65px must reach it.


def _seg_0402__sr_sts(*, M: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 402 (sr_sts) - body verbatim from the legacy gate() (feature 022)."""
    sr_sts = M.get("town_streets", [])
    return _kept(locals(), ('sr_sts',))


def _seg_0403__sr_bad() -> dict[str, Any]:
    """Gate segment 403 (sr_bad) - body verbatim from the legacy gate() (feature 022)."""
    sr_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('sr_bad',))


# alley ENDS answer to the same rule - the S band's roji visibly dangled short of (and
# past) the band street they aim at (GM 2026-08-10, the render's most repeated defect)
# LANES were absent from this list entirely (GM 2026-08-11, reporting the same near-miss a
# second time), so a lane's ends were never examined by any of the tests below - which looks
# exactly like a lane that passes. Alleys were here; lanes, the wider of the two, were not.


def _seg_0404__al9(*, M: Any = _UNBOUND, al9: Any = _UNBOUND, ln9: Any = _UNBOUND, sr_sts: Any = _UNBOUND, st9: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 404 (al9, ln9, sr_enders, st9) - body verbatim from the legacy gate() (feature 022)."""
    sr_enders = (
        [(st9, st9.get("w", 18) / 2, True) for st9 in sr_sts]
        + [(al9, al9.get("w", 10) / 2, False) for al9 in M.get("alleys", [])]
        + [(ln9, ln9.get("w", 10) / 2, False) for ln9 in M.get("lanes", []) if isinstance(ln9, dict)]
    )
    return _kept(locals(), ('al9', 'ln9', 'sr_enders', 'st9'))


def _seg_0405__E9(
    *,
    E9: Any = _UNBOUND,
    a9: Any = _UNBOUND,
    align9: Any = _UNBOUND,
    ang_self: Any = _UNBOUND,
    b9: Any = _UNBOUND,
    cp9: Any = _UNBOUND,
    cp9c: Any = _UNBOUND,
    cross9: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    dl9: Any = _UNBOUND,
    gap9: Any = _UNBOUND,
    gd9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    meta: Any = _UNBOUND,
    nb9: Any = _UNBOUND,
    ot9: Any = _UNBOUND,
    ot_bear9: Any = _UNBOUND,
    otw9: Any = _UNBOUND,
    perp9: Any = _UNBOUND,
    q9: Any = _UNBOUND,
    sr_bad: Any = _UNBOUND,
    sr_bear: Any = _UNBOUND,
    sr_best: Any = _UNBOUND,
    sr_crossed: Any = _UNBOUND,
    sr_enders: Any = _UNBOUND,
    sr_hw2: Any = _UNBOUND,
    sr_is_street: Any = _UNBOUND,
    sr_len9: Any = _UNBOUND,
    sr_myhw: Any = _UNBOUND,
    sr_ot9: Any = _UNBOUND,
    sr_sts: Any = _UNBOUND,
    st9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 405 (E9, a9, align9, ang_self) - body verbatim from the legacy gate() (feature 022)."""
    for st9, sr_myhw, sr_is_street in sr_enders:
        if len(st9.get("pts") or []) < 2:
            continue  # a one-vertex way has no direction of travel to aim with
        for E9, nb9 in ((st9["pts"][0], st9["pts"][1]), (st9["pts"][-1], st9["pts"][-2])):
            sr_best: tuple[float, float, Pt, float] = (1e9, 0.0, (0.0, 0.0), 0.0)  # type: ignore[no-redef]
            for ot9 in sr_sts:
                if ot9 is st9:
                    continue
                for k9 in range(len(ot9["pts"]) - 1):
                    d9 = seg_dist(E9[0], E9[1], ot9["pts"][k9], ot9["pts"][k9 + 1])
                    if d9 < sr_best[0]:
                        cp9c = seg_closest(E9[0], E9[1], ot9["pts"][k9], ot9["pts"][k9 + 1])
                        sr_bear = math.degrees(math.atan2(ot9["pts"][k9 + 1][1] - ot9["pts"][k9][1], ot9["pts"][k9 + 1][0] - ot9["pts"][k9][0]))
                        sr_best = (d9, ot9.get("w", 18) / 2, (float(cp9c[0]), float(cp9c[1])), sr_bear)
            if sr_best[0] >= 1e9:
                continue
            d9, otw9, cp9, ot_bear9 = sr_best
            gap9 = d9 - sr_myhw - otw9
            if not (gap9 > 2 and d9 < 95):
                continue
            dl9 = math.hypot(E9[0] - nb9[0], E9[1] - nb9[1]) or 1.0
            gd9 = math.hypot(cp9[0] - E9[0], cp9[1] - E9[1]) or 1.0
            align9 = ((E9[0] - nb9[0]) / dl9) * ((cp9[0] - E9[0]) / gd9) + ((E9[1] - nb9[1]) / dl9) * ((cp9[1] - E9[1]) / gd9)
            # ALIGNMENT IS NOT THE ONLY TELL (GM 2026-08-10: "two city streets which approach
            # each other... generally should intersect"). A street ending a short way off
            # another it meets at a CORNER angle is a junction that failed to close, whatever
            # its end happens to point at - which is how a slightly slanted run slipped past the
            # aligned-only test. So: aligned and close, OR near-perpendicular and very close.
            perp9 = False
            if gd9 > 1:
                ang_self = math.degrees(math.atan2(E9[1] - nb9[1], E9[0] - nb9[0]))
                cross9 = abs((ang_self - ot_bear9) % 180.0)
                # only for a STREET: an alley legitimately dead-ends inside a block (a roji
                # serves the core it threads and stops), so a blind alley near a parallel street
                # is not a failed junction. A STREET carries through-traffic and should close.
                # ...and only if the two do not ALREADY cross somewhere: a street's free end
                # often lies near a perpendicular street it met 70px back, and calling that a
                # failed junction is how this rule first tried to truncate five sound streets
                sr_crossed = False
                for sr_ot9 in sr_sts:
                    if sr_ot9 is st9:
                        continue
                    if min(seg_dist(E9[0], E9[1], sr_ot9["pts"][k9], sr_ot9["pts"][k9 + 1]) for k9 in range(len(sr_ot9["pts"]) - 1)) > d9 + 1:
                        continue
                    # CONNECTED, not merely crossing: a pair that meets at an ENDPOINT (a T) never
                    # registers as a segment crossing, and treating those as failed junctions is
                    # how this rule first proposed truncating five sound streets
                    sr_hw2 = sr_myhw + sr_ot9.get("w", 18) / 2 + 3
                    if (
                        any(
                            segments_cross(tuple(st9["pts"][a9]), tuple(st9["pts"][a9 + 1]), tuple(sr_ot9["pts"][b9]), tuple(sr_ot9["pts"][b9 + 1]))
                            for a9 in range(len(st9["pts"]) - 1)
                            for b9 in range(len(sr_ot9["pts"]) - 1)
                        )
                        or any(seg_dist(q9[0], q9[1], sr_ot9["pts"][b9], sr_ot9["pts"][b9 + 1]) < sr_hw2 for q9 in (st9["pts"][0], st9["pts"][-1]) for b9 in range(len(sr_ot9["pts"]) - 1))
                        or any(
                            # ...and SYMMETRICALLY: the other street's end may be the one lying on
                            # this street's body, which is the commoner T of the two
                            seg_dist(q9[0], q9[1], st9["pts"][a9], st9["pts"][a9 + 1]) < sr_hw2
                            for q9 in (sr_ot9["pts"][0], sr_ot9["pts"][-1])
                            for a9 in range(len(st9["pts"]) - 1)
                        )
                    ):
                        sr_crossed = True
                        break
                # A LONG lane is a through-way, not a roji (GM 2026-08-11, reporting the same
                # defect twice: "it stops just short of intersecting"). The alley exemption above
                # is right for a short service thread that dies inside the block it serves, and
                # WRONG for a 470 px lane that runs the depth of a quarter and halts 90 ft off a
                # major street. Measured in real feet so it means the same thing at every tier.
                sr_len9 = sum(math.dist(st9["pts"][k9], st9["pts"][k9 + 1]) for k9 in range(len(st9["pts"]) - 1)) * float(meta.get("ftpx", 1))
                perp9 = (sr_is_street or sr_len9 > 600.0) and not sr_crossed and 45.0 < min(cross9, 180.0 - cross9) <= 90.0 and d9 < 80.0
            if (align9 > 0.6 and d9 < 65.0) or perp9:
                sr_bad.append((round(E9[0]), round(E9[1]), round(d9)))
    return _kept(
        locals(),
        (
            'E9',
            'a9',
            'align9',
            'ang_self',
            'b9',
            'cp9',
            'cp9c',
            'cross9',
            'd9',
            'dl9',
            'gap9',
            'gd9',
            'k9',
            'nb9',
            'ot9',
            'ot_bear9',
            'otw9',
            'perp9',
            'q9',
            'sr_bad',
            'sr_bear',
            'sr_best',
            'sr_crossed',
            'sr_hw2',
            'sr_is_street',
            'sr_len9',
            'sr_myhw',
            'sr_ot9',
            'st9',
        ),
    )


def _seg_0406__city_streets_reach_their_neighbors(*, check: Any = _UNBOUND, sr_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 406 (city_streets_reach_their_neighbors) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "city_streets_reach_their_neighbors",
        not sr_bad,
        f"street end(s) stopping a visible gap short of the street they point at (x, y, px): {sorted(set(sr_bad))[:4]} - extend the end to the exact junction (compute the segment intersection), or turn/shorten it so it clearly is not aiming there",
    )
    return _kept(locals(), ())


# WAYS CLEAR OF THE CASTLE'S OWN MOAT (GM 2026-08-10: a city street started 6px off the
# castle moat's channel line - the CITY moat battery never read the castle record).


def _seg_0407__cm_bad() -> dict[str, Any]:
    """Gate segment 407 (cm_bad) - body verbatim from the legacy gate() (feature 022)."""
    cm_bad = []  # type: ignore[var-annotated]
    return _kept(locals(), ('cm_bad',))


def _seg_0408__cm9(
    *,
    M: Any = _UNBOUND,
    cm9: Any = _UNBOUND,
    cm_bad: Any = _UNBOUND,
    cm_defw: Any = _UNBOUND,
    cm_kind: Any = _UNBOUND,
    cm_list: Any = _UNBOUND,
    cmw9: Any = _UNBOUND,
    cs9: Any = _UNBOUND,
    cw9: Any = _UNBOUND,
    cw_pts: Any = _UNBOUND,
    cw_w: Any = _UNBOUND,
    d9: Any = _UNBOUND,
    k9: Any = _UNBOUND,
    p9: Any = _UNBOUND,
) -> dict[str, Any]:
    """Gate segment 408 (cm9, cm_bad, cm_defw, cm_kind) - body verbatim from the legacy gate() (feature 022)."""
    for cs9 in M.get("castles", []):
        cm9 = cs9.get("moat")
        if not cm9 or len(cm9) < 3:
            continue
        cmw9 = float(cs9.get("moat_width", 22))
        for cm_kind, cm_list, cm_defw in (("street", M.get("town_streets", []), 18), ("alley", M.get("alleys", []), 10), ("lane", M.get("lanes", []), 10)):
            for cw9 in cm_list:
                cw_pts = cw9["pts"] if isinstance(cw9, dict) else cw9
                cw_w = cw9.get("w", cm_defw) if isinstance(cw9, dict) else cm_defw
                for p9 in cw_pts:
                    d9 = min(seg_dist(p9[0], p9[1], cm9[k9], cm9[(k9 + 1) % len(cm9)]) for k9 in range(len(cm9)))
                    if d9 < cmw9 / 2 + cw_w / 2:
                        cm_bad.append((cm_kind, round(p9[0]), round(p9[1])))
                        break
    return _kept(locals(), ('cm9', 'cm_bad', 'cm_defw', 'cm_kind', 'cm_list', 'cmw9', 'cs9', 'cw9', 'cw_pts', 'cw_w', 'd9', 'k9', 'p9'))


def _seg_0409__ways_clear_of_castle_moat(*, check: Any = _UNBOUND, cm_bad: Any = _UNBOUND) -> dict[str, Any]:
    """Gate segment 409 (ways_clear_of_castle_moat) - body verbatim from the legacy gate() (feature 022)."""
    check(
        "ways_clear_of_castle_moat",
        not cm_bad,
        f"way vertex(es) in the castle moat's channel: {sorted(set(cm_bad))[:4]} - the keep's moat is water like any other; start/route the way clear of the channel band (only the castle's own gate bridges cross it)",
    )
    return _kept(locals(), ())
