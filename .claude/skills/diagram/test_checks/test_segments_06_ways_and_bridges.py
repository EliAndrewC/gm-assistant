"""Split from test_checks.py by feature 025 - see test_checks/CLAUDE.md for the index."""

from test_checks._builders import WALLSQ, _bridge_map, _capital_manifest, _skew_bridge_map, f, house


def test_roads_bridge_water_fires_when_unbridged():
    # the road runs straight through the stream with no bridge
    assert "roads_bridge_water" in f(_bridge_map([]))


def test_roads_bridge_water_passes_when_bridged():
    assert "roads_bridge_water" not in f(_bridge_map([{"x": 500, "y": 500, "rot": 0, "span": 37, "w": 26}]))


def test_roads_bridge_water_passes_when_road_runs_alongside_water():
    # a road parallel to a stream, never intersecting it, needs no bridge
    M = {"meta": {"scale": "village", "W": 1000, "H": 1000}, "road": [[100, 480], [900, 480]], "streams": [{"poly": [[100, 520], [900, 520]], "frm": None, "to": None, "w": 9}], "bridges": []}
    assert "roads_bridge_water" not in f(M)


def test_roads_bridge_water_fires_on_an_unbridged_lane_over_a_canal():
    # a village LANE crossing an irrigation ditch must be bridged too (not only roads/streets)
    M = {
        "meta": {"scale": "village", "W": 1000, "H": 1000},
        "lanes": [{"pts": [[100, 500], [900, 500]], "w": 6}],
        "field_ditches": [{"poly": [[500, 100], [500, 900]], "w": 5, "role": "main", "field": "p"}],
        "bridges": [],
    }
    assert "roads_bridge_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 0, "span": 32, "w": 6}]
    assert "roads_bridge_water" not in f(M)


def test_roads_bridge_water_fires_where_the_ring_road_crosses_the_cargo_canal():
    """The RING ROAD is a carried way and the CARGO CANAL is a watercourse.

    Neither was in the crossing scan until 2026-07-27, so a city's ring-over-canal crossing was
    invisible to this check AND to s.bridges() - which is why Minami's and Nagahara's were
    hand-placed and both went crooked."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000},
        "ring_road": [[100, 500], [900, 500]],
        "ring_road_width": 7,
        "canals": [{"poly": [[500, 100], [500, 900]], "w": 12}],
        "bridges": [],
    }
    assert "roads_bridge_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 0, "span": 40, "w": 7}]
    assert "roads_bridge_water" not in f(M)


def test_roads_bridge_water_ignores_an_undrawn_conduit_channel():
    """An UNDRAWN channel (topo_channel's `drawn: False`) is a buried conduit recorded for water
    topology - there is no seam on the ground, so a way over its line crosses nothing. Tango's ring
    road runs over three of them; demanding decks there would put timber over a drain nobody can see."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000},
        "ring_road": [[100, 500], [900, 500]],
        "ring_road_width": 7,
        "channels": [{"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "w": 2.5, "drawn": False}],
        "bridges": [],
    }
    assert "roads_bridge_water" not in f(M)
    M["channels"][0]["drawn"] = True  # ...but a channel that IS dug and drawn must be carried over
    assert "roads_bridge_water" in f(M)


def test_roads_bridge_water_fires_on_an_unbridged_trunk_road_over_the_city_moat():
    """M["roads"] - every trunk road but the Imperial one - crossing the MOAT. Both the drawer and
    the checker omitted the roads list until feature 020 factored the carried-ways and
    crossed-waters sets into ONE shared source (settlement.bridge_carried_ways /
    bridge_crossed_waters): the two agreed perfectly and were both wrong, and four of six
    crossings on the first capital were unbridged with a green gate."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000},
        "roads": [{"pts": [[100, 500], [900, 500]], "w": 26}],
        "moat": [[500, 100], [500, 900]],
        "moat_width": 22,
        "bridges": [],
    }
    assert "roads_bridge_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 0, "span": 50, "w": 26}]
    assert "roads_bridge_water" not in f(M)


def test_roads_bridge_water_fires_on_an_unbridged_road_over_the_river():
    """The trunk RIVER, in the shape s.river() actually records: a streams entry plus the
    M['river'] dict carrying 'pts' (not 'poly' - the shared source reads both). A road crossing
    a river was never bridged anywhere in the pool before feature 020."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000},
        "road": [[100, 500], [900, 500]],
        "river": {"pts": [[500, 100], [500, 900]], "w": 40},
        "streams": [{"poly": [[500, 100], [500, 900]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}, "w": 40}],
        "bridges": [],
    }
    assert "roads_bridge_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 0, "span": 68, "w": 26}]
    assert "roads_bridge_water" not in f(M)


def test_roads_bridge_water_fires_on_an_unbridged_way_over_a_castle_moat():
    """A castle's OWN moat is water like any other - the capital's ceremonial avenue crosses it
    at the ote-mon, and that crossing was invisible to both sides until the shared source."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000},
        "roads": [{"pts": [[100, 500], [900, 500]], "w": 30}],
        "castles": [{"x": 500, "y": 250, "w": 120, "h": 90, "rot": 0, "gate": [500, 295], "moat": [[500, 420], [500, 900]], "moat_width": 26, "label": "Castle"}],
        "bridges": [],
    }
    assert "roads_bridge_water" in f(M)
    M["bridges"] = [{"x": 500, "y": 500, "rot": 0, "span": 54, "w": 30}]
    assert "roads_bridge_water" not in f(M)


def test_watercourse_crosses_wall_at_water_gate():
    """A watercourse pierces a rampart ONLY at a water gate (GM 2026-08-09: Nagahara's canal had
    drifted 40px off its gate and ran under the wall - an index-anchored moat vertex moved in a
    past re-roll and nothing compared the crossing to the gap). The doctrine was already written
    in inwall_drain_outfall's docstring; this is its check."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000},
        "wall": [[300, 300], [700, 300], [700, 700], [300, 700]],
        "water_gates": [{"x": 700, "y": 500, "w": 36, "h": 22, "rot": 0, "z": 1}],
        "canals": [{"poly": [[900, 500], [650, 500]], "w": 12}],  # through the gate
    }
    assert "watercourse_crosses_wall_at_water_gate" not in f(M)
    M["canals"] = [{"poly": [[900, 560], [650, 560]], "w": 12}]  # under the wall, 60px off the gate
    assert "watercourse_crosses_wall_at_water_gate" in f(M)
    M["canals"] = [{"poly": [[900, 560], [650, 560]], "w": 12, "drawn": False}]  # a buried culvert pierces nothing
    assert "watercourse_crosses_wall_at_water_gate" not in f(M)


def test_gate_roads_join_the_ring_fires_on_a_stub_and_passes_when_joined():
    """A gate's road must JOIN the ring road, not stop on the sill (GM 2026-08-09: the
    capital's side-gate trunk roads STARTED at the gate point, so the gate opened onto 90 ft
    of bare ground inside the wall). A way joins by a vertex near the ring or by crossing it."""
    ring = [[130, 130], [870, 130], [870, 870], [130, 870], [130, 130]]
    M = {"meta": {"scale": "city"}, "ring_road": ring, "gates": [[500, 100]], "roads": [{"pts": [[50, 50], [60, 60]], "w": 8}, {"pts": [[500, 100], [500, 0]], "w": 26}]}
    assert "gate_roads_join_the_ring" in f(M)  # the road runs outward only - a stub on the sill
    M["roads"][1]["pts"] = [[500, 134], [500, 100], [500, 0]]  # extended inward, vertex on the ring
    assert "gate_roads_join_the_ring" not in f(M)
    M["roads"][1]["pts"] = [[500, 200], [500, 0]]  # or the way CROSSES the ring outright
    assert "gate_roads_join_the_ring" not in f(M)


def test_bridges_align_with_their_way_passes_a_solved_deck():
    # a deck seated on the crossing and bearing with the road - what s.bridges() produces
    assert "bridges_align_with_their_way" not in f(_skew_bridge_map())
    # ...and a deck may point either way along the road: a plank has no forward direction
    assert "bridges_align_with_their_way" not in f(_skew_bridge_map(rot=180))


def test_bridges_align_with_their_way_fires_on_a_skewed_deck():
    # GM 2026-07-27, Minami's cargo basin: the deck was 39 deg off the way it carried, so the road
    # read as running straight through the water past a crooked plank
    fails = f(_skew_bridge_map(rot=39))
    assert "bridges_align_with_their_way" in fails
    assert "roads_bridge_water" not in fails  # the older rule is satisfied by ANY deck within 40px - that is the gap


def test_bridges_align_with_their_way_fires_on_a_deck_beside_its_crossing():
    # seated 17px east of where the way actually meets the water (Minami's offset), correctly angled
    fails = f(_skew_bridge_map(x=517))
    assert "bridges_align_with_their_way" in fails
    assert "roads_bridge_water" not in fails


def test_bridges_align_with_their_way_fires_on_a_deck_that_carries_nothing():
    # a deck over water with no way on it at all: either the way or the watercourse is unrecorded
    M = _bridge_map([{"x": 500, "y": 500, "rot": 0, "span": 37, "w": 26}])
    del M["road"]
    assert "bridges_align_with_their_way" in f(M)


def test_bridges_align_with_their_way_exempts_standalone_footplanks():
    """A `foot` plank is carried by no way and crosses its ditch PERPENDICULAR by construction, so
    the alignment rule would fire on every correct one. Its own rules are long_ditches_have_a_
    footbridge and footbridges_reach_useful_ground."""
    M = _skew_bridge_map(rot=90, foot=True)  # square across the road it is nowhere near carrying
    assert "bridges_align_with_their_way" not in f(M)


# ---- feature 021: the capital housing layer ---------------------------------------------------


def test_capital_districts_declared_fires_when_fabric_stands_undeclared():
    """Once dwellings stand, the capital records which district each pack filled (T003) - the
    rank-gradient check's ground truth. The bare 020 state (no fabric) stays legal."""
    M = _capital_manifest()
    assert "capital_districts_declared" not in f(M)  # no fabric yet - legal
    M["houses"] = [house(500, 500)]
    assert "capital_districts_declared" in f(M)
    M["districts"] = [{"name": "east machi", "kind": "machi", "poly": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]}]
    assert "capital_districts_declared" not in f(M)


def test_capital_rank_gradient_fires_on_an_inverted_band():
    """The jokamachi law (research 021 item 1): walled yashiki nearest the castle, retainer
    terraces at the band edge. Red: the yashiki band's members sit BEYOND the terrace band's."""
    M = _capital_manifest()
    M["castles"] = [{"x": 200, "y": 200, "w": 100, "h": 80}]
    M["districts"] = [
        {"name": "west bank", "kind": "yashiki", "rank_band": "yashiki", "poly": [[700, 100], [900, 100], [900, 300], [700, 300]]},
        {"name": "castle foot", "kind": "terrace", "rank_band": "terrace", "poly": [[250, 100], [450, 100], [450, 300], [250, 300]]},
    ]
    M["manors"] = [{"x": 800, "y": 200, "w": 60, "h": 40, "label": "Hazama Estate"}]
    M["terraces"] = [{"x": 300, "y": 200, "w": 36, "h": 7, "rot": 0, "units": 5, "z": 1}]
    assert "capital_rank_gradient" in f(M)
    M["districts"][0]["poly"], M["districts"][1]["poly"] = M["districts"][1]["poly"], M["districts"][0]["poly"]
    M["manors"][0]["x"], M["terraces"][0]["x"] = 300, 800
    assert "capital_rank_gradient" not in f(M)


def test_terraces_are_ranges_fires_on_a_single_unit():
    """A one-unit terrace is a detached house miscoded (T005) - the range record models one
    roof over several household cells."""
    M = _capital_manifest()
    M["terraces"] = [{"x": 500, "y": 500, "w": 6, "h": 7, "rot": 0, "units": 1, "z": 1}]
    assert "terraces_are_ranges" in f(M)
    M["terraces"][0]["units"] = 6
    assert "terraces_are_ranges" not in f(M)


def test_capital_housing_matches_band_targets_fires_on_a_band_shortfall():
    """T006: the 018 budget is the housing authority - each band's drawn count lands on its
    dwelling_target (max(2, 5%) tolerance), so a quietly-short band fires by name."""
    M = _capital_manifest()
    M["meta"]["budget"]["dwelling_target"] = {"samurai_yashiki": 5, "samurai_detached": 0, "samurai_terrace": 0, "packed": 0, "dwellings": 5}
    M["districts"] = [{"name": "castle foot", "kind": "yashiki", "rank_band": "yashiki", "poly": [[0, 0], [1000, 0], [1000, 1000], [0, 1000]]}]
    M["manors"] = [{"x": 300, "y": 300, "w": 60, "h": 40, "label": "Hazama Estate"}]
    assert "capital_housing_matches_band_targets" in f(M)  # 1 drawn vs 5
    M["manors"] += [{"x": 300 + 80 * i, "y": 500, "w": 60, "h": 40, "label": "Estate"} for i in range(4)]
    assert "capital_housing_matches_band_targets" not in f(M)


def test_cistern_wells_sit_on_the_buried_main():
    """Research 021 item 4: josui-ido tap the mokuhi mains that run UNDER THE STREETS from
    the settling basin at the gate - so a cistern-well stands within the band (~600 real ft
    of the terminus, the disclosed calibrated liberty) and beside a street. A dug draw-well
    (no kind) is untouched."""
    M = _capital_manifest()
    M["aqueducts"] = [{"poly": [[900, 100], [700, 300]], "w": 8, "intake": [900, 100], "to": [700, 300]}]
    M["town_streets"] = [{"pts": [[700, 300], [700, 700]], "w": 5}]
    M["wells"] = [{"x": 705, "y": 420, "r": 8, "vr": 6, "shrine": False, "private": False, "kind": "cistern"}]
    assert "cistern_wells_in_service_band" not in f(M)  # on the street, 120px from the basin
    M["wells"][0]["x"], M["wells"][0]["y"] = 705, 620  # 320px out - beyond the main's reach
    assert "cistern_wells_in_service_band" in f(M)
    M["wells"][0]["x"], M["wells"][0]["y"] = 760, 380  # in reach but 55px off any street
    assert "cistern_wells_in_service_band" in f(M)
    M["wells"][0].pop("kind")  # a dug draw-well may stand anywhere wells stand
    assert "cistern_wells_in_service_band" not in f(M)


def test_kido_close_the_machi_mouths():
    """Research 021 item 6 (the ward MESH): every street mouth into a machi district gets its
    night-barred kido; a mouth without one fires. The mouths come from the SAME shared source
    the placer uses (settlement.machi_mouths), so the two sides cannot disagree."""
    M = _capital_manifest()
    M["districts"] = [{"name": "east machi", "kind": "machi", "poly": [[300, 300], [700, 300], [700, 700], [300, 700]]}]
    M["town_streets"] = [{"pts": [[100, 500], [900, 500]], "w": 5}]  # crosses at (300,500) and (700,500)
    assert "kido_close_the_machi_mouths" in f(M)  # two mouths, no kido
    M["kido"] = [{"x": 312, "y": 500, "parts": [], "guard": None}, {"x": 688, "y": 500, "parts": [], "guard": None}]
    assert "kido_close_the_machi_mouths" not in f(M)


def test_precinct_interiors_within_reservation():
    """T017 red-green: a declared precinct must draw >= 5 halls inside its reserved rect; a
    dormitory overhanging the reservation fires."""
    M = _capital_manifest()
    M["precincts"] = [{"x": 500, "y": 500, "w": 130, "h": 100, "rear": "north", "graveyard": False}]
    assert "precinct_interiors_within_reservation" in f(M)  # declared, nothing drawn
    halls = [
        {"x": 456, "y": 462, "w": 16, "h": 10, "kind": "residence", "precinct": [500, 500]},
        {"x": 455, "y": 480, "w": 12, "h": 8, "kind": "kitchen", "precinct": [500, 500]},
        {"x": 492, "y": 460, "w": 19, "h": 7, "kind": "dormitory", "precinct": [500, 500]},
        {"x": 514, "y": 472, "w": 19, "h": 7, "kind": "dormitory", "precinct": [500, 500]},
        {"x": 552, "y": 498, "w": 11, "h": 8, "kind": "library", "precinct": [500, 500]},
        {"x": 446, "y": 502, "w": 14, "h": 9, "kind": "administration", "precinct": [500, 500]},
    ]
    M["precinct_halls"] = halls
    assert "precinct_interiors_within_reservation" not in f(M)
    M["precinct_halls"] = halls[:-1] + [{"x": 570, "y": 502, "w": 14, "h": 9, "kind": "administration", "precinct": [500, 500]}]
    assert "precinct_interiors_within_reservation" in f(M)  # administration overhangs east edge


def test_precinct_graveyard_claims_closed():
    """T017 red-green: a temple with graveyard=True and no burial plot within 230px fires; the
    drawn plot closes the 020 claim."""
    M = _capital_manifest()
    M["precincts"] = [{"x": 500, "y": 500, "w": 130, "h": 100, "rear": "north", "graveyard": True}]
    M["precinct_halls"] = [{"x": 456 + i, "y": 462, "w": 4, "h": 4, "kind": k, "precinct": [500, 500]} for i, k in enumerate(("residence", "kitchen", "dormitory", "dormitory", "library"))]
    M["religious"] = [{"kind": "temple", "x": 500, "y": 500, "w": 50, "h": 33, "label": "Temple of Benten", "graveyard": True}]
    assert "precinct_graveyard_claims_closed" in f(M)
    M["cemeteries"] = [{"x": 544, "y": 464, "w": 24, "h": 16, "rot": 0, "parish": True}]  # rot: the capital now runs the funerary block (GM 2026-08-10)
    assert "precinct_graveyard_claims_closed" not in f(M)


def test_monzen_fronts_the_approach():
    """T018 red-green: a monzen district on the temple's blind side (no torii inside) fires; on
    the approach with its commercial rows it passes."""
    M = _capital_manifest()
    M["precincts"] = [{"x": 500, "y": 500, "w": 130, "h": 100, "rear": "north", "graveyard": False}]
    M["precinct_halls"] = [{"x": 456 + i, "y": 462, "w": 4, "h": 4, "kind": k, "precinct": [500, 500]} for i, k in enumerate(("residence", "kitchen", "dormitory", "dormitory", "library"))]
    M["torii"] = [(500, 580), (500, 620)]  # the sando marches SOUTH
    shops = [{"kind": "shop", "x": 460 + 12 * i, "y": 600, "w": 8, "h": 6} for i in range(7)]
    M["buildings"] = M.get("buildings", []) + shops
    M["districts"] = (M.get("districts") or []) + [{"name": "blind monzen", "kind": "monzen", "poly": [[430, 380], [570, 380], [570, 445], [430, 445]]}]
    assert "monzen_fronts_the_approach" in f(M)  # north of the temple, torii face south
    M["districts"][-1] = {"name": "monzen", "kind": "monzen", "poly": [[430, 560], [570, 560], [570, 640], [430, 640]]}
    assert "monzen_fronts_the_approach" not in f(M)


def test_teramachi_backstrip_lean():
    """T019 red-green: a packed dwelling between a rim temple and the rampart fires; a
    monk_house there is the temple's own and passes."""
    M = _capital_manifest()
    wallx = max(p9[0] for p9 in M["wall"])
    ty = sum(p9[1] for p9 in M["wall"]) / len(M["wall"])
    M["religious"] = (M.get("religious") or []) + [{"kind": "temple", "x": wallx - 130, "y": ty, "w": 32, "h": 21, "label": "Temple of Ebisu"}]
    M["buildings"] = M.get("buildings", []) + [{"kind": "laborer", "x": wallx - 60, "y": ty, "w": 10, "h": 7}]
    assert "teramachi_backstrip_lean" in f(M)
    M["buildings"][-1]["kind"] = "monk_house"
    assert "teramachi_backstrip_lean" not in f(M)


def test_capital_packed_band_is_validated_as_two_bands_not_one_total():
    """The wall-resize lesson (GM 2026-08-10): a correct TOTAL must not hide an in-wall
    shortfall spilled into the suburbs - and that specific combination names its own cure."""
    M = _capital_manifest()
    M["meta"]["budget"]["dwelling_target"] = {"packed": 100, "packed_suburb": 30, "samurai_yashiki": 0, "samurai_detached": 0, "samurai_terrace": 0}
    M["districts"] = [
        {"name": "in machi", "kind": "machi", "poly": [[100, 100], [900, 100], [900, 900], [100, 900]]},
        {"name": "out ward", "kind": "machi", "poly": [[1200, 100], [1600, 100], [1600, 900], [1200, 900]]},
    ]

    def _pk(n, x0):
        return [{"kind": "laborer", "x": x0 + 14 * (i % 20), "y": 120 + 14 * (i // 20), "w": 10, "h": 7} for i in range(n)]

    M["buildings"] = _pk(70, 120) + _pk(30, 1220)  # 70 in-wall + 30 suburban = the budget's split
    r = f(M)
    assert "capital_housing_matches_band_targets" not in r
    M["buildings"] = _pk(40, 120) + _pk(60, 1220)  # total still 100 - but the wall cannot hold its band

    fails = f(M)
    assert "capital_housing_matches_band_targets" in fails


def test_capital_interior_slack_in_band():
    """The wall-settles-first rule (GM 2026-08-10): claimed-open ground beyond 15% of the
    interior names the wall oversized and demands re-derivation BEFORE fine iteration."""
    M = _capital_manifest()
    M["commons"] = [{"poly": [[100, 100], [700, 100], [700, 700], [100, 700]], "role": "pasture", "x": 400, "y": 400, "w": 600, "h": 600}]
    r = f(M)
    assert "capital_interior_slack_in_band" in r  # 36% of a 1M interior
    M["commons"][0]["poly"] = [[100, 100], [400, 100], [400, 400], [100, 400]]  # 9%
    assert "capital_interior_slack_in_band" not in f(M)


def test_monzen_floor_fires_on_too_few_commercial_buildings():
    """A monzen with its torii but a bare handful of shops is not doing a monzen's job - the
    elif branch of monzen_fronts_the_approach (coverage: the no-torii branch had a test, the
    too-few-commerce branch did not)."""
    M = _capital_manifest()
    M["precincts"] = [{"x": 500, "y": 500, "w": 130, "h": 100, "rear": "north", "graveyard": False}]
    M["precinct_halls"] = [{"x": 456 + i, "y": 462, "w": 4, "h": 4, "kind": k, "precinct": [500, 500]} for i, k in enumerate(("residence", "kitchen", "dormitory", "dormitory", "library"))]
    M["torii"] = [(500, 580), (500, 620)]
    M["districts"] = (M.get("districts") or []) + [{"name": "thin monzen", "kind": "monzen", "poly": [[430, 560], [570, 560], [570, 650], [430, 650]]}]
    M["buildings"] = M.get("buildings", []) + [{"x": 460, "y": 600, "w": 8, "h": 6, "kind": "shop", "rot": 0}]  # torii inside, but ONE shop
    assert "monzen_fronts_the_approach" in f(M)


def test_wells_not_clustered():
    """GM 2026-08-10: the capital had knots of 4-6 wellheads together, unlike every other pool
    map (all max at 4 inside a 150 ft radius). Accretion from chasing a local household count."""
    spread = {"meta": {"scale": "city", "ftpx": 3}, "wells": [{"x": 100 + 200 * i, "y": 100, "kind": None} for i in range(6)]}
    assert "wells_not_clustered" not in f(spread)
    knot = {"meta": {"scale": "city", "ftpx": 3}, "wells": [{"x": 500 + 9 * i, "y": 500 + 7 * i, "kind": None} for i in range(6)]}
    assert "wells_not_clustered" in f(knot)


def test_extramural_features_tethered_and_gate_markets_start_at_their_gate():
    """GM 2026-08-10: "the kiln works is wayyyyy out in the middle of nowhere" and "the gate
    markets look pretty far from the actual gates". Everything outside a wall belongs to
    something - a gate, a road it hauls on, or the wharf - and a gate market crowds its gate."""
    base = {
        "meta": {"scale": "city", "walled": True, "W": 3000, "H": 3000, "ftpx": 3},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "roads": [{"pts": [[500, 200], [500, -400]], "w": 9}],
    }
    assert "extramural_features_tethered" in f({**base, "kilns": [{"x": 2400, "y": 2400, "w": 30, "h": 20, "rot": 0}]})
    assert "extramural_features_tethered" not in f({**base, "kilns": [{"x": 520, "y": -150, "w": 30, "h": 20, "rot": 0}]})
    shops_far = [{"x": 500 + 20 * i, "y": -55, "w": 10, "h": 8, "rot": 0, "kind": "shop"} for i in range(4)]  # 255px out: inside the market reach, past the head allowance
    assert "gate_markets_start_at_their_gate" in f({**base, "buildings": shops_far})
    shops_at = [{"x": 500 + 20 * i, "y": 130, "w": 10, "h": 8, "rot": 0, "kind": "shop"} for i in range(4)]
    assert "gate_markets_start_at_their_gate" not in f({**base, "buildings": shops_at})


def test_animal_yards_clear_of_compound_gates():
    """GM 2026-08-10: no samurai wants dung piles at their front door. Measured to the GATE
    POINT, so a yard behind the compound's back wall is ordinary city ground."""
    manor = {"x": 500, "y": 500, "w": 100, "h": 80, "rot": 0, "gate_dir": "south", "label": "Test Estate"}
    at_gate = {"meta": {"scale": "city", "ftpx": 3}, "manors": [manor], "stable_yards": [{"x": 500, "y": 580, "r": 40, "of": [500, 580], "troughs": 1, "rails": []}]}
    assert "animal_yards_clear_of_compound_gates" in f(at_gate)
    behind = {"meta": {"scale": "city", "ftpx": 3}, "manors": [manor], "stable_yards": [{"x": 500, "y": 380, "r": 40, "of": [500, 380], "troughs": 1, "rails": []}]}
    assert "animal_yards_clear_of_compound_gates" not in f(behind)


def test_map_frame_hugs_its_content():
    """GM 2026-08-10: a stale per-side crop override (south=240, east=700) left dead margin on
    two flanks. Each side of the view needs real drawn content within 260 ft of the edge."""
    tight = {
        "meta": {"scale": "city", "ftpx": 3, "view": [0, 0, 900, 900]},
        "buildings": [{"x": 20, "y": 20, "w": 8, "h": 6, "rot": 0, "kind": "laborer"}, {"x": 880, "y": 880, "w": 8, "h": 6, "rot": 0, "kind": "laborer"}],
    }
    assert "map_frame_hugs_its_content" not in f(tight)
    loose = {
        "meta": {"scale": "city", "ftpx": 3, "view": [0, 0, 900, 3000]},
        "buildings": [{"x": 20, "y": 20, "w": 8, "h": 6, "rot": 0, "kind": "laborer"}, {"x": 880, "y": 400, "w": 8, "h": 6, "rot": 0, "kind": "laborer"}],
    }
    assert "map_frame_hugs_its_content" in f(loose)


def test_ways_cross_water_on_a_deck():
    """GM 2026-08-10: "roads should not overlap with water without a bridge present." Unlike
    roads_bridge_water this reads EVERY drawn way (alleys and lanes included) and tests bed
    OVERLAP, not centerline crossing - the capital's shore path lay in the moat drain with no
    plank and the crossing rule never saw it."""
    base = {"meta": {"scale": "city", "ftpx": 3}, "streams": [{"poly": [[0, 500], [1000, 500]], "w": 20}]}
    assert "ways_cross_water_on_a_deck" in f({**base, "alleys": [{"pts": [[400, 300], [400, 700]], "w": 10}]})
    decked = {**base, "alleys": [{"pts": [[400, 300], [400, 700]], "w": 10}], "bridges": [{"x": 400, "y": 500, "rot": 90, "span": 34, "w": 10}]}
    assert "ways_cross_water_on_a_deck" not in f(decked)
    assert "ways_cross_water_on_a_deck" not in f({**base, "alleys": [{"pts": [[400, 300], [400, 460]], "w": 10}]})


def test_new_2026_08_10_check_edge_cases():
    """Degenerate shapes the GM-review checks must survive, and the wall-reach clause that keeps
    a works on the near farm ground legal: a one-point way, a compound with an unknown gate
    side, a malformed yard record, and a kiln 900 ft from the wall with no road under it."""
    water = {"meta": {"scale": "city", "ftpx": 3}, "streams": [{"poly": [[0, 500], [1000, 500]], "w": 20}]}
    # a one-vertex way has no segment to sample - it must not raise, and must not fire
    assert "ways_cross_water_on_a_deck" not in f({**water, "alleys": [{"pts": [[400, 500]], "w": 10}]})
    # gate_dir the mapping does not know, and a yard record with no x
    odd = {
        "meta": {"scale": "city", "ftpx": 3},
        "manors": [{"x": 500, "y": 500, "w": 100, "h": 80, "rot": 0, "gate_dir": "northeast", "label": "Odd Estate"}],
        "stable_yards": [{"x": 500, "y": 900, "r": 40, "of": [500, 900], "troughs": 1, "rails": [], "troughs_at": [500, 900]}],
    }
    assert "animal_yards_clear_of_compound_gates" not in f(odd)
    # the wall-reach clause: a works on the near farm ground, no road under it, is tethered
    near = {
        "meta": {"scale": "city", "walled": True, "W": 3000, "H": 3000, "ftpx": 3},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "kilns": [{"x": 500, "y": 1000, "w": 30, "h": 20, "rot": 0}],
    }
    assert "extramural_features_tethered" not in f(near)  # 200px past the wall = 600 ft
    far = {**near, "kilns": [{"x": 500, "y": 1400, "w": 30, "h": 20, "rot": 0}]}
    assert "extramural_features_tethered" in f(far)  # 600px = 1,800 ft, past the attested band


def test_sluice_gates_centered_on_their_channel():
    """GM 2026-08-10, after the SAME defect recurred: a sluice gate's frame spans BANK TO BANK,
    so its center must sit on the channel's CENTERLINE - not merely inside the water's band.
    The old rule measured to the bank, so a gate two-thirds of a half-width off-center passed
    while reading as detached from the water it gates."""
    on = {"meta": {"scale": "city", "ftpx": 3}, "streams": [{"poly": [[0, 500], [1000, 500]], "w": 22}], "sluice_gates": [{"x": 500, "y": 501, "rot": 90}]}
    assert "sluice_gates_centered_on_their_channel" not in f(on)
    off = {**on, "sluice_gates": [{"x": 500, "y": 516, "rot": 90}]}  # 16px off a 22px channel
    assert "sluice_gates_centered_on_their_channel" in f(off)


def test_frontage_shops_face_their_way():
    """GM 2026-08-10: one shop in the north gate market's row faced away from the road while its
    four neighbors faced it. A storefront IS its street face."""
    base = {"meta": {"scale": "city", "ftpx": 3}, "roads": [{"pts": [[0, 100], [1000, 100]], "w": 20}]}
    facing = {**base, "buildings": [{"x": 500, "y": 140, "w": 12, "h": 9, "rot": 180, "kind": "shop"}]}
    assert "frontage_shops_face_their_way" not in f(facing)
    away = {**base, "buildings": [{"x": 500, "y": 140, "w": 12, "h": 9, "rot": 0, "kind": "shop"}]}
    assert "frontage_shops_face_their_way" in f(away)
    interior = {**base, "buildings": [{"x": 500, "y": 400, "w": 12, "h": 9, "rot": 0, "kind": "shop"}]}
    assert "frontage_shops_face_their_way" not in f(interior)


def test_captions_sit_by_their_feature_and_clear_the_defenses():
    """GM 2026-08-10: the settling-basin caption sat ON the city wall and the intake-weir caption
    far from its weir. One rule keeps a caption BY what it names; the other keeps it off the
    rampart, whose ink swallows the text and which the caption would otherwise appear to name."""
    base = {"meta": {"scale": "city", "ftpx": 3}, "streams": [{"poly": [[0, 500], [1000, 500]], "w": 20}]}
    near = {**base, "sluice_gates": [{"x": 500, "y": 500, "rot": 0}], "labels": [[470, 470, 540, 480, 1, "sluice gate"]]}
    assert "captions_sit_by_their_feature" not in f(near)
    far = {**base, "sluice_gates": [{"x": 500, "y": 500, "rot": 0}], "labels": [[900, 200, 970, 210, 1, "sluice gate"]]}
    assert "captions_sit_by_their_feature" in f(far)
    on_wall = {"meta": {"scale": "city", "ftpx": 3}, "wall": WALLSQ, "labels": [[770, 470, 830, 480, 1, "settling basin"]]}  # straddles the x=800 wall face
    assert "captions_clear_of_the_defenses" in f(on_wall)
    off_wall = {"meta": {"scale": "city", "ftpx": 3}, "wall": WALLSQ, "labels": [[600, 470, 680, 480, 1, "settling basin"]]}
    assert "captions_clear_of_the_defenses" not in f(off_wall)


def test_city_streets_serve_both_sides():
    """GM 2026-08-10: "several city streets extend out into empty space with nothing on either
    side of them and also not leading to anywhere... essentially a road to nowhere check."
    city_streets_have_buildings measures ONE side and excuses claimed open ground; this one
    fires when a long stretch is bare on BOTH."""
    base = {"meta": {"scale": "city", "walled": True, "W": 2000, "H": 2000, "ftpx": 3}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]]}
    bare = {**base, "town_streets": [{"pts": [[300, 400], [900, 400]], "w": 18}]}
    assert "city_streets_serve_both_sides" in f(bare)
    lined = {
        **base,
        "town_streets": [{"pts": [[300, 400], [900, 400]], "w": 18}],
        "buildings": [{"x": 320 + 60 * i, "y": 360, "w": 14, "h": 10, "rot": 0, "kind": "laborer"} for i in range(11)],
    }
    assert "city_streets_serve_both_sides" not in f(lined)


def test_new_checks_skip_degenerate_records():
    """The 2026-08-10 checks tolerate the shapes a real manifest holds: an INLAND store that is
    not a waterside work, a label tuple too short to carry text, and a one-vertex road."""
    water = {"meta": {"scale": "city", "ftpx": 3}, "streams": [{"poly": [[0, 500], [1000, 500]], "w": 20}]}
    assert "waterside_works_follow_the_bank" not in f({**water, "granaries": [{"x": 500, "y": 900, "w": 20, "h": 12, "rot": 0}]})
    assert "roads_join_the_network" not in f({"meta": {"scale": "city", "ftpx": 3, "W": 1000, "H": 1000}, "roads": [{"pts": [[500, 500]], "w": 20}]})
    # LEGACY LABEL RECORDS: the regression corpus holds manifests whose labels predate the text
    # field. Removing this guard on the evidence of live maps alone crashed the gate before five
    # fixtures reached their own check, and they silently stopped firing (2026-08-10).
    legacy = {"meta": {"scale": "city", "ftpx": 3}, "wall": WALLSQ, "sluice_gates": [{"x": 500, "y": 500, "rot": 0}], "labels": [[760, 470, 840, 480, 7]]}
    assert "captions_sit_by_their_feature" not in f(legacy)
    assert "captions_clear_of_the_defenses" not in f(legacy)


def test_funerary_ground_within_reach_and_one_complex():
    """GM 2026-08-10, researched: nothing in the record holds the funerary ground far off the
    wall - ritual pollution is satisfied by being outside at all (Kyoto's Injo-ji stood ON the
    Odoi rampart), a pyre's codified setback is 50 ft, and what set the distance was worthless
    ground on the road out. The complex BEGINS just past the wall and runs outward, and the
    three features are ONE ground (Kozukappara held all three within ~290 ft)."""
    base = {"meta": {"scale": "capital", "walled": True, "W": 4000, "H": 4000, "ftpx": 3}, "wall": WALLSQ, "gates": [[500, 200]]}
    near = {**base, "cemeteries": [{"x": 500, "y": 900, "w": 60, "h": 40, "rot": 0}], "cremation_grounds": [{"x": 560, "y": 940, "w": 40, "h": 30, "rot": 0}]}
    assert "funerary_ground_within_reach" not in f(near)
    assert "funerary_complex_is_one_ground" not in f(near)
    far = {**base, "cemeteries": [{"x": 500, "y": 1300, "w": 60, "h": 40, "rot": 0}]}
    assert "funerary_ground_within_reach" in f(far)  # 500px past the wall = 1,500 ft
    split = {**near, "cremation_grounds": [{"x": 1400, "y": 900, "w": 40, "h": 30, "rot": 0}]}
    assert "funerary_complex_is_one_ground" in f(split)


def test_extramural_housing_serves_its_work():
    """GM 2026-08-10: worker housing outside the wall exists to put hands next to the quay, the
    granaries or the gate market - "the whole point of those houses being outside the city
    instead of inside of it is that those are the housing for the workers who work those
    facilities." A row across the channel from all of it is a suburb with no reason."""
    base = {"meta": {"scale": "city", "walled": True, "W": 3000, "H": 3000, "ftpx": 3}, "wall": WALLSQ, "gates": [[500, 200]], "granaries": [{"x": 500, "y": 1000, "w": 20, "h": 12, "rot": 0}]}
    beside = {**base, "buildings": [{"x": 520 + 12 * i, "y": 1040, "w": 10, "h": 7, "rot": 0, "kind": "laborer"} for i in range(6)]}
    assert "extramural_housing_serves_its_work" not in f(beside)
    across = {**base, "buildings": [{"x": 1800 + 12 * i, "y": 2200, "w": 10, "h": 7, "rot": 0, "kind": "laborer"} for i in range(6)]}
    assert "extramural_housing_serves_its_work" in f(across)


def test_streets_reach_neighbors_catches_perpendicular_approaches():
    """GM 2026-08-10: "two city streets which approach each other... generally should
    intersect." The aligned-only test missed a street ending a short way off one it meets at a
    CORNER angle - and the first cut of the perpendicular test compared the end's bearing
    against the LINE OF SIGHT to the other street, which makes two parallel streets 60px apart
    look perpendicular. It must compare against the other street's own bearing."""
    base = {"meta": {"scale": "city", "walled": True, "W": 2000, "H": 2000, "ftpx": 3}, "wall": WALLSQ, "gates": [[500, 200]]}
    tee = {**base, "town_streets": [{"pts": [[400, 300], [400, 900]], "w": 10}, {"pts": [[470, 600], [900, 600]], "w": 10}]}
    assert "city_streets_reach_their_neighbors" in f(tee)  # the east street stops 70px off the north-south one
    joined = {**base, "town_streets": [{"pts": [[400, 300], [400, 900]], "w": 10}, {"pts": [[402, 600], [900, 600]], "w": 10}]}
    assert "city_streets_reach_their_neighbors" not in f(joined)
    parallel = {**base, "town_streets": [{"pts": [[400, 300], [400, 900]], "w": 10}, {"pts": [[460, 300], [460, 900]], "w": 10}]}
    assert "city_streets_reach_their_neighbors" not in f(parallel)  # 60px apart and PARALLEL - not a failed junction
