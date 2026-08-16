"""Split from test_checks.py by feature 025 - see test_checks/CLAUDE.md for the index."""

from tests.check_village._builders import (
    _CITY_WALL,
    _MOAT_FEEDER,
    _MOAT_OUTFALL,
    WALLSQ,
    _capital_manifest,
    _caravan_city,
    _city_with_samurai,
    _drain_city,
    _es_pocket_city,
    _farmhouse,
    _feeder_city,
    _field,
    _fort_city,
    _grove,
    _street_city,
    bldg,
    f,
)


def test_no_groves_inside_walls_fires():
    M = {"meta": {"scale": "city", "walled": True}, "wall": _CITY_WALL, "houses": [_farmhouse(500, 500)], "groves": [_grove(465, 470, 500, 500)]}  # of (500,500) is inside the wall
    assert "no_groves_inside_walls" in f(M)


def test_no_groves_inside_walls_passes_for_an_outside_farm():
    M = {"meta": {"scale": "city", "walled": True}, "wall": _CITY_WALL, "houses": [_farmhouse(1200, 500)], "groves": [_grove(1165, 470, 1200, 500)]}  # of (1200,500) is outside
    assert "no_groves_inside_walls" not in f(M)


def test_city_labels_placed_with_subject_fires_when_label_is_across_the_wall():
    # the samurai cluster is INSIDE the wall but its label floats OUTSIDE (over the moat) - misleading
    M = _city_with_samurai([850, 492, 950, 508, 0, "samurai neighborhood"])  # center (900,500), outside WALLSQ
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_fires_when_label_far_from_cluster():
    # label inside the wall but nowhere near its samurai houses (they are at ~(420,420), label at (730,720))
    M = _city_with_samurai([680, 712, 780, 728, 0, "samurai neighborhood"])
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_fires_when_label_over_a_field():
    # burakumin houses sit just south, but the label floats over a paddy to their north
    field = {"name": "f", "kind": "paddy", "bbox": [360, 360, 520, 520], "outline": [[360, 360], [520, 360], [520, 520], [360, 520]]}
    bur = [bldg(420, 540, kind="burakumin"), bldg(460, 540, kind="burakumin"), bldg(440, 500, kind="burakumin")]
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "buildings": bur,
        "fields": [field],
        "labels": [[390, 442, 490, 458, 0, "burakumin neighborhood"]],
    }  # center (440,450), inside field f
    assert "city_labels_placed_with_subject" in f(M)


def test_city_labels_placed_with_subject_skips_labels_with_no_known_subject():
    # a zone-suffix label whose subject we can't identify ("potters district" - no such building kind)
    # cannot be verified, so it is skipped rather than flagged
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "labels": [[850, 492, 950, 508, 0, "potters district"]]}
    assert "city_labels_placed_with_subject" not in f(M)


def test_city_labels_placed_with_subject_passes_when_among_the_cluster():
    # label inside the wall AND among its samurai houses (center ~(420,410)) - the correct placement
    M = _city_with_samurai([370, 402, 470, 418, 0, "samurai neighborhood"])
    assert "city_labels_placed_with_subject" not in f(M)


def test_city_flophouse_in_humble_quarter_fires_next_to_merchants():
    # an in-wall flophouse cheek-by-jowl with a merchant house - a doss-house does not belong in the
    # nicer quarter
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
        "buildings": [bldg(560, 500, kind="merchant")],
    }  # merchant 60px away
    assert "city_flophouse_in_humble_quarter" in f(M)


def test_city_flophouse_in_humble_quarter_fires_next_to_burakumin():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
        "buildings": [bldg(580, 500, kind="burakumin")],
    }  # burakumin 80px away (in/beside the quarter)
    assert "city_flophouse_in_humble_quarter" in f(M)


def test_city_flophouse_in_humble_quarter_passes_when_humble_and_clear():
    # in-wall flophouse with only laborers nearby - the humble sector, correctly placed
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [{"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0}],
        "buildings": [bldg(560, 500, kind="laborer"), bldg(540, 560, kind="laborer")],
    }
    assert "city_flophouse_in_humble_quarter" not in f(M)


def test_city_canal_reaches_dock_fires_when_short_and_passes_when_it_feeds_the_basin():
    # the canal must connect the water to the dock basin (like a street reaching the road)
    river = {"pts": [[900, 100], [900, 900]], "w": 40}
    dock = [{"x": 400, "y": 500, "w": 54, "h": 34, "rot": 0}]
    short = _fort_city(river=river, docks=dock, canals=[{"poly": [[884, 500], [460, 500]], "w": 14}])  # stops 33px short of the dock
    assert "city_canal_reaches_dock" in f(short)
    reach = _fort_city(river=river, docks=dock, canals=[{"poly": [[884, 500], [418, 500]], "w": 14}])  # end sits in the basin
    assert "city_canal_reaches_dock" not in f(reach)


def test_city_canal_shares_moat_mouth_fires_on_a_second_mouth_and_passes_on_the_moat_handoff():
    # GM 2026-07-23 (Nagahara's water-gate corner): the cargo canal opened its OWN river mouth
    # 36 real ft beside the moat's downstream junction, riding collinearly inside the moat arm's
    # stroke - a smeared doubled channel. The Suzhou pattern shares ONE mouth: the canal ends ON
    # the moat, and the moat's downstream river junction is the navigation entrance. The real
    # pre-fix manifest is frozen in pool/regressions/.
    river = {"pts": [[900, 100], [900, 900]], "w": 40}
    dock = [{"x": 400, "y": 500, "w": 54, "h": 34, "rot": 0}]
    moat = [[894, 496], [700, 500], [600, 600], [894, 800]]  # open arc, both ends on the river
    doubled = _fort_city(river=river, docks=dock, moat=moat, moat_width=22, canals=[{"poly": [[884, 508], [418, 500]], "w": 14}])  # own river mouth inside the moat arm's corridor
    assert "city_canal_shares_moat_mouth" in f(doubled)
    handoff = _fort_city(river=river, docks=dock, moat=moat, moat_width=22, canals=[{"poly": [[700, 500], [418, 500]], "w": 14}])  # ends ON the moat: the shared mouth
    fails = f(handoff)
    assert "city_canal_shares_moat_mouth" not in fails
    assert "city_canal_reaches_dock" not in fails  # the moat handoff satisfies "reaches the water"


def test_city_moat_junction_angles_fires_on_square_tees_and_passes_when_tilted():
    # GM 2026-07-24 (Nagahara hydrology review): both moat-river junctions met the river as
    # identical square tees - an rfoot-projection artifact. The outlet must sweep downstream
    # (confluences merge at downstream angles; a square tee drives the exit jet across the
    # river) and the inlet must stay square-to-upstream (a flow-aligned intake drinks bedload).
    # The real pre-tilt manifest is frozen in pool/regressions/.
    river = {"pts": [[900, 100], [900, 900]], "w": 40}  # upstream-first: flows N -> S
    square = _fort_city(river=river, moat=[[894, 300], [700, 300], [700, 800], [894, 800]], moat_width=22)
    assert "city_moat_junction_angles" in f(square)  # the outlet meets the river as a square tee
    tilted = _fort_city(river=river, moat=[[894, 260], [700, 300], [700, 800], [894, 860]], moat_width=22)
    assert "city_moat_junction_angles" not in f(tilted)  # inlet tilted upstream, outlet swept downstream


def test_city_wharf_jetties_on_bank_fires_when_floating_and_passes_on_the_bank():
    # a jetty is a finger from the near bank into the water, not a bar floating mid-stream
    river = {"pts": [[900, 100], [900, 900]], "w": 40}  # centerline x900, near (city) bank x880
    fire = _fort_city(river=river, jetties=[{"x": 860, "y": 500, "rot": 0, "len": 80}])
    assert "city_wharf_jetties_on_bank" in f(fire)
    ok = _fort_city(river=river, jetties=[{"x": 876, "y": 500, "rot": 0, "len": 18}])  # root at the bank, tip in the near water
    assert "city_wharf_jetties_on_bank" not in f(ok)


def test_log_boom_checks_fire_on_the_mid_stream_chain_and_pass_on_a_bank_pen():
    # GM 2026-08-02 (Minami): "it just looks like a bunch of logs in the middle of the river."
    # The pre-fix boom floated mid-channel - adrift AND crowding the fairway (the real capture is
    # frozen in pool/regressions/). The redesigned pen hugs the near bank (bank on local +y; rot 90
    # turns +y toward the west shore), takes a third of the channel, and leaves the fairway clear.
    river = {"pts": [[900, 100], [900, 900]], "w": 40}  # centerline x900, banks x880/x920
    fire = _fort_city(river=river, log_booms=[{"x": 900, "y": 500, "rot": 90, "len": 100}])  # pre-2026-08 record shape: no pen_w
    hits = f(fire)
    assert "log_boom_moored_to_the_bank" in hits and "log_boom_leaves_the_fairway" in hits
    ok = _fort_city(river=river, log_booms=[{"x": 886.6, "y": 500, "rot": 90, "len": 100, "pen_w": 13.3}])
    hits2 = f(ok)
    assert "log_boom_moored_to_the_bank" not in hits2 and "log_boom_leaves_the_fairway" not in hits2
    # teeth against a center-collapse: the ok pen's CENTER sits 13.4px off the centerline (a center
    # measure would read it 6.7px off the bank line and condemn it) while the fire chain's center is
    # exactly ON the centerline - only the derived corners judge both correctly


def test_log_boom_serves_the_lumber_yard_ties_pen_to_yard():
    # boom and zaimokuya are one works: the pen is the yard's waterside holding ground
    river = {"pts": [[900, 100], [900, 900]], "w": 40}
    pen = [{"x": 886.6, "y": 500, "rot": 90, "len": 100, "pen_w": 13.3}]
    near = _fort_city(river=river, log_booms=pen, lumber_yards=[{"x": 940, "y": 520, "w": 30, "h": 20, "rot": 0, "label": "lumber yard"}])
    assert "log_boom_serves_the_lumber_yard" not in f(near)
    far = _fort_city(river=river, log_booms=pen, lumber_yards=[{"x": 400, "y": 400, "w": 30, "h": 20, "rot": 0, "label": "lumber yard"}])
    assert "log_boom_serves_the_lumber_yard" in f(far)


def test_city_streets_have_buildings_fires_on_an_empty_city_street():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "town_streets": [{"pts": [[300, 300], [700, 300]], "w": 20}]}
    assert "city_streets_have_buildings" in f(M)


def test_city_streets_have_buildings_ignores_frontage_across_a_ward_fence():
    # the buildings hug the street (60px away) but a ward fence runs BETWEEN them and it: they front
    # whatever lies on their own side, not this street, so the street still reads as empty and fires.
    # (This is the Tango government-avenue bug: gap-band housing across the ward fence papered over a
    # bare avenue. A building walled off from a street cannot count as fronting it.)
    blds = [bldg(320 + i * 40, 440, kind="laborer") for i in range(9)]  # y440: 60px N of the street, N of the fence
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 20}],
        "wards": [{"name": "x", "boundary": [[280, 470], [720, 470]]}],  # fence between the houses and the street
        "buildings": blds,
    }
    assert "city_streets_have_buildings" in f(M)


def test_city_larger_streets_lined_fires_on_a_bare_street():
    # a main avenue through open ground inside the wall, no buildings within ~58px of it
    assert "city_larger_streets_lined" in f(_street_city([{"pts": [[300, 500], [700, 500]], "w": 22, "main": True}]))


def test_city_larger_streets_lined_passes_when_lined():
    # the same avenue, shophouses lining it ~32px off on both sides
    blds = [bldg(x, 500 + s * 32, kind="shop", w=20, h=14) for x in range(320, 701, 40) for s in (-1, 1)]
    assert "city_larger_streets_lined" not in f(_street_city([{"pts": [[300, 500], [700, 500]], "w": 22, "main": True}], buildings=blds))


def test_city_larger_streets_lined_exempts_a_government_avenue():
    # a bare avenue, but two ministry compounds front it -> a government avenue, exempt (its frontage
    # is the spaced ministries, governed by city_ministries_front_a_street, not shops/houses)
    M = _street_city([{"pts": [[300, 500], [700, 500]], "w": 18}], ministries=[{"name": "A", "x": 400, "y": 565, "w": 88, "h": 58}, {"name": "B", "x": 620, "y": 565, "w": 88, "h": 58}])
    assert "city_larger_streets_lined" not in f(M)


def test_city_gate_caravan_facilities_fires_without_inn_and_stables():
    # a gate with only a flophouse - no prominent inn, no large stables for the wagon-trains' animals
    M = _caravan_city(flophouses=[{"x": 500, "y": 300, "w": 88, "h": 42, "rot": 0}])
    assert "city_gate_caravan_facilities" in f(M)


def test_city_gate_caravan_facilities_passes_with_the_full_cluster():
    M = _caravan_city(
        flophouses=[{"x": 450, "y": 300, "w": 88, "h": 42, "rot": 0}],
        buildings=[{"x": 520, "y": 320, "w": 66, "h": 48, "kind": "inn", "rot": 0}, {"x": 470, "y": 380, "w": 92, "h": 44, "kind": "stables", "rot": 0}],
    )
    assert "city_gate_caravan_facilities" not in f(M)


def test_city_gate_caravan_facilities_fires_when_stables_hemmed_in():
    # the full cluster is present, but the stables is hemmed in by dwellings (no open ground for animals)
    blds = [{"x": 470, "y": 380, "w": 92, "h": 44, "kind": "stables", "rot": 0}, {"x": 520, "y": 320, "w": 66, "h": 48, "kind": "inn", "rot": 0}]
    blds += [bldg(440 + i * 22, 380, kind="samurai") for i in range(6)]  # dwellings crowd the stables
    M = _caravan_city(flophouses=[{"x": 450, "y": 300, "w": 88, "h": 42, "rot": 0}], buildings=blds)
    assert "city_gate_caravan_facilities" in f(M)


def test_city_streets_connected_and_empty_space_fire():
    # two town streets far apart with no road -> two disconnected groups; the interior is almost
    # all empty (no buildings/fields), and a pond sits on a grid point (the pond-as-occupancy path)
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100], [500, 900]],
        "town_streets": [{"pts": [[200, 200], [200, 400]], "w": 18}, {"pts": [[700, 600], [700, 800]], "w": 18}],
        "pond": [400, 400, 80, 60],
    }
    fails = f(M)
    assert "city_streets_connected" in fails
    assert "city_no_large_empty_space" in fails


def test_city_no_large_empty_space_fires_on_an_unclaimed_pocket():
    # the footprint-aware rebuild (GM 2026-07-23, Tango's north gate): a pocket far smaller than
    # the old vast-void threshold still fires when nothing claims it
    assert "city_no_large_empty_space" in f(_es_pocket_city())


def test_city_no_large_empty_space_passes_when_an_animal_ground_claims_the_pocket():
    # the standing remedy: the SAME pocket goes green once a stable-yard / animal-ground record
    # claims the open ground as deliberate working space (s.animal_ground)
    M = _es_pocket_city(stable_yards=[{"x": 600, "y": 480, "r": 80.0, "of": [600, 480]}])
    assert "city_no_large_empty_space" not in f(M)


def test_city_has_dye_works_fires_when_the_yard_is_far_from_water():
    # a dyer's yard needs rinsing/vat water ON site - a yard in the dry middle of town fails even
    # though one exists (settlements.md "TRADE WORKS"; the presence branch is covered by the pinned
    # pre-trades city fixtures)
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3, "walled": True},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100]],
        "streams": [{"poly": [[0, 950], [1000, 950]], "w": 12}],  # far south, ~400px away
        "dye_yards": [{"x": 500, "y": 500, "w": 27, "h": 17, "rot": 0, "label": "dye works"}],
    }
    assert "city_has_dye_works" in f(M)


def test_city_kiln_outside_walls_fires_on_an_intramural_kiln():
    # fire law + smoke: a kiln INSIDE the rampart is the defect even though a kiln exists
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3, "walled": True},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100]],
        "kilns": [{"x": 500, "y": 500, "w": 46.7, "h": 40, "rot": 0, "label": "kiln"}],
    }
    assert "city_kiln_outside_walls" in f(M)


def test_city_bathhouse_count_follows_the_population_formula():
    # GM formula 2026-07-24 (second refinement): 1 sento per full 2,000 population + a
    # remainder-fraction chance of one extra (Edo's peak ratio, ~1 per ~2,100 residents);
    # a recorded roll must match the drawn count
    def city(pop, n_baths, roll=None):
        meta = {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3, "walled": True, "population": pop}
        if roll is not None:
            meta["bathhouse_roll"] = roll
        return {
            "meta": meta,
            "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
            "gates": [[500, 100]],
            "bathhouses": [{"x": 400 + 60 * i, "y": 500, "w": 16, "h": 16, "rot": 0, "label": "bathhouse"} for i in range(n_baths)],
        }

    assert "city_has_bathhouse" in f(city(4000, 1))  # 4,000 = two full units, zero remainder: exactly 2
    assert "city_has_bathhouse" in f(city(2000, 2))  # 2,000 = one full unit, zero remainder: exactly 1
    assert "city_has_bathhouse" in f(city(2500, 3))  # 2,500 allows 1 or 2 (25% extra), never 3
    assert "city_has_bathhouse" in f(city(3000, 1, roll=2))  # the drawn count must match the recorded roll
    assert "city_has_bathhouse" not in f(city(3000, 2, roll=2))  # in-formula and roll-matched passes
    assert "city_has_bathhouse" not in f(city(2500, 2, roll=2))  # the remainder extra landed
    assert "city_has_bathhouse" not in f(city(3000, 1, roll=1))


def test_city_river_port_has_lumber_yard_fires_when_missing_and_skips_landlocked():
    # a river-port city (meta river_port) must keep a riverside zaimokuya; a landlocked city
    # skips the check entirely (the GM's Tango/Nagahara split - timber moves by water at scale)
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3, "walled": True, "river_port": True},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100]],
    }
    assert "city_river_port_has_lumber_yard" in f(M)
    M["meta"] = {"scale": "city", "W": 1000, "H": 1000, "ftpx": 3, "walled": True}
    assert "city_river_port_has_lumber_yard" not in f(M)


def test_city_streets_connected_fires_on_a_gap_wider_than_45px():
    # two parallel streets 60px apart: the old 95px tolerance bridged them, the tightened 45px
    # does not - a grid that stops short of the road reads as a separated network, not connected
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[400, 300], [400, 700]], "w": 18}, {"pts": [[460, 300], [460, 700]], "w": 18}],
    }  # 60px apart, no road bridge
    assert "city_streets_connected" in f(M)


def test_city_streets_connected_requires_beds_to_actually_overlap():
    # a cross-street whose end stops 30px short of the through-street: under the old flat 45px
    # tolerance this "connected", but the two paved beds (half-widths 9+9) do not touch, so you
    # cannot walk between them - it is a separate network. This is the Tango laborer-grid bug.
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [
            {"pts": [[300, 400], [700, 400]], "w": 18},  # the through-street
            {"pts": [[400, 430], [400, 700]], "w": 18},
        ],
    }  # ends 30px below it: beds 18px apart
    assert "city_streets_connected" in f(M)


def test_city_flophouse_inside_walls_fires_when_only_outside():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [{"x": 500, "y": 120, "w": 92, "h": 42, "rot": 0}, {"x": 500, "y": 880, "w": 92, "h": 42, "rot": 0}],
    }
    assert "city_flophouse_inside_walls" in f(M)


def test_city_flophouse_outside_each_gate_fires_when_a_gate_lacks_one():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "flophouses": [
            {"x": 500, "y": 500, "w": 92, "h": 42, "rot": 0},  # inside
            {"x": 500, "y": 120, "w": 92, "h": 42, "rot": 0},
        ],
    }  # outside the north gate only
    assert "city_flophouse_outside_each_gate" in f(M)


def test_city_estates_multiple_shown_fires_when_none_in_view():
    # PADDY-FIRST doctrine (GM 2026-07-23): ONE estate in view suffices (the rest sit farther out,
    # implied off-map) - so the check fires only when NO estate shows at all.
    M = {
        "meta": {"scale": "city", "walled": True, "W": 3000, "H": 3000, "view": [0, 0, 1000, 1000]},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "manors": [
            {"x": 1600, "y": 1600, "w": 100, "h": 80},
            {"x": 2000, "y": 2000, "w": 100, "h": 80},
        ],
    }  # both off the cropped view
    assert "city_estates_multiple_shown" in f(M)


def test_city_estates_multiple_shown_passes_with_a_single_estate_in_view():
    # the paddy-first floor: a lone estate (even a fraction at the frame edge) is the accurate signal
    M = {
        "meta": {"scale": "city", "walled": True, "W": 3000, "H": 3000, "view": [0, 0, 1000, 1000]},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "manors": [
            {"x": 990, "y": 600, "w": 100, "h": 80},  # a fraction inside the view edge
            {"x": 2000, "y": 2000, "w": 100, "h": 80},
        ],
    }
    assert "city_estates_multiple_shown" not in f(M)


def test_city_road_label_outside_walls_fires_when_inside():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "road_label": [500, 500]}  # dead center, inside the walls
    assert "city_road_label_outside_walls" in f(M)


def test_city_streets_no_near_miss_fires_on_a_sliver_gap():
    # two street segments ~18px apart that do NOT cross - they almost touch but never meet
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [
            {"pts": [[300, 400], [500, 400]], "w": 18},  # ends at (500, 400)
            {"pts": [[515, 410], [515, 700]], "w": 18},
        ],
    }  # top at (515, 410): an ~18px gap
    assert "city_streets_no_near_miss" in f(M)


def test_city_streets_no_intersection_stub_fires_on_a_short_overshoot():
    # a vertical street crosses a horizontal one and then stops 25px past it - a dangling stub
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [
            {"pts": [[300, 500], [700, 500]], "w": 18},  # horizontal cross-street
            {"pts": [[450, 300], [450, 525]], "w": 18},
        ],
    }  # crosses at y500, stops at 525 (25px past)
    assert "city_streets_no_intersection_stub" in f(M)


def test_city_streets_no_intersection_stub_passes_when_streets_run_well_past():
    # the same crossing, but the vertical street continues well past (to 700) - a real grid line
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18}, {"pts": [[450, 300], [450, 700]], "w": 18}],
    }
    assert "city_streets_no_intersection_stub" not in f(M)


def test_city_torii_over_streets_fires_when_torii_under_street():
    # a torii on the street but with a LOWER draw-z than the street -> the street paints over it
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "torii": [[500, 500, 50]],  # z = 50
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 18, "z": 100}],
    }  # z = 100 > torii -> torii underneath
    assert "city_torii_over_streets" in f(M)


def test_city_temple_approach_has_torii_fires_when_street_runs_up_without_one():
    # a street terminates right at the temple front but there is no torii arch on it
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "religious": [{"kind": "temple", "label": "T", "x": 500, "y": 500, "w": 100, "h": 80}],
        "town_streets": [{"pts": [[500, 700], [500, 545]], "w": 18}],
    }  # runs up to the south edge (540)
    assert "city_temple_approach_has_torii" in f(M)


def test_view_treats_the_crop_as_the_map_edge():
    # the Imperial road must run off the map edge through both gates. With a cropped city view,
    # "the edge" is the view, not the full canvas - a road that exits the view (but not the
    # canvas) counts as running through.
    base = {
        "meta": {"scale": "city", "walled": True, "W": 3000, "H": 2000},
        "wall": [[1300, 300], [1700, 300], [1700, 1700], [1300, 1700]],
        "gates": [[1500, 300], [1500, 1700]],
        "road": [[1500, 250], [1500, 1750]],
    }  # exits y250..1750, well inside the 0..2000 canvas
    assert "city_imperial_road_through" in f(base)  # no view: road stops short of the canvas edge
    base["meta"]["view"] = [1250, 280, 500, 1440]  # crop to y280..1720
    assert "city_imperial_road_through" not in f(base)  # road now exits the view -> runs through


def test_city_civic_clear_of_streets_fires():
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000},
        "wall": WALLSQ,
        "gates": [[500, 200], [500, 800]],
        "ministries": [{"x": 500, "y": 500, "w": 90, "h": 60, "name": "Ministry of War"}],
        "town_streets": [{"pts": [[300, 500], [700, 500]], "w": 20}],
    }  # the street runs through the ministry
    assert "city_civic_clear_of_streets" in f(M)


def test_city_outside_field_and_gate_market_fire():
    ff = {"name": "ff", "kind": "paddy", "bbox": [1500, 1500, 1800, 1800], "outline": [[1500, 1500], [1800, 1500], [1800, 1800], [1500, 1800]]}
    M = {"meta": {"scale": "city", "walled": True, "W": 2000, "H": 2000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [ff]}
    fails = f(M)
    assert "city_outside_fields_have_farmhouses" in fails
    assert "city_fields_close_to_city" in fails
    assert "city_has_gate_market" in fails


def test_city_gate_guardhouse_and_moat_irrigation_fire():
    bigf = {"name": "bf", "kind": "paddy", "bbox": [960, 200, 1180, 900], "outline": [[960, 200], [1180, 200], [1180, 900], [960, 900]]}
    M = {
        "meta": {"scale": "city", "walled": True, "W": 1300, "H": 1100},
        "wall": [[100, 100], [900, 100], [900, 900], [100, 900]],
        "gates": [[500, 100], [500, 900]],
        "moat": [[80, 80], [920, 80], [920, 920], [80, 920], [80, 80]],
        "fields": [bigf],
    }
    fails = f(M)
    assert "city_gate_has_guardhouse" in fails  # no gate structures
    assert "city_moat_irrigates_fields" in fails  # big outside field, no channel feeds it


def test_city_no_inwall_farms_fires_without_agricultural_district():
    # a field whose centroid sits inside the wall, and no meta(agricultural_district=True)
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [_field("f", 400, 400, 600, 600)]}
    assert "city_no_inwall_farms" in f(M)


def test_city_no_inwall_farms_allowed_with_agricultural_district():
    M = {"meta": {"scale": "city", "walled": True, "agricultural_district": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "fields": [_field("f", 400, 400, 600, 600)]}
    assert "city_no_inwall_farms" not in f(M)


def test_city_moat_checks_fire_when_moat_neither_surrounds_nor_is_fed():
    M = {"meta": {"scale": "city", "walled": True, "W": 1000, "H": 1000}, "wall": WALLSQ, "gates": [[500, 200], [500, 800]], "moat": [[400, 400], [600, 400], [600, 600], [400, 600]]}
    fails = f(M)
    assert "city_moat_surrounds_wall" in fails  # a tiny moat INSIDE the wall does not encircle it
    assert "city_moat_fed_offmap" in fails  # no stream feeds it


def test_city_moat_feeder_matches_width_fires_when_narrow():
    # a 9px trickle reaching a 22px moat - too thin to keep it supplied
    assert "city_moat_feeder_matches_width" in f(_feeder_city(9))


def test_city_moat_feeder_matches_width_passes_when_matched():
    assert "city_moat_feeder_matches_width" not in f(_feeder_city(22))


def test_city_moat_has_outfall_passes_with_a_flush_through_ring():
    # feeder on the W rim + outfall on the E rim (opposite faces) = a flow-through moat; the extra
    # in-city ditch does NOT reach the moat, so it is not mistaken for a tap
    inland = {"poly": [[500, 480], [500, 520]], "frm": None, "to": None, "w": 6}
    assert "city_moat_has_outfall" not in f(_drain_city([_MOAT_FEEDER, _MOAT_OUTFALL, inland]))


def test_city_moat_has_outfall_fires_when_a_fed_moat_cannot_drain():
    # a full-flow feeder into a closed moat with no outfall - conservation of flow, it would overflow
    assert "city_moat_has_outfall" in f(_drain_city([_MOAT_FEEDER]))


def test_streets_may_front_open_ground():
    """021: a street along a commons (the castle's cleared ring, a festival ground) serves that
    ground - it is not a bare stretch. Without the commons the same street fires."""
    M = _capital_manifest(scale="city")
    M["meta"]["walled"] = True  # the urban battery (where both street checks live) binds walled cities
    M["buildings"] = [b for b in M.get("buildings", []) if not 700 < b["y"] < 1100]  # bare band for the test street
    M["town_streets"] = (M.get("town_streets") or []) + [{"pts": [[300, 900], [900, 900]], "w": 15}]
    r = f(M)
    fired = "city_streets_have_buildings" in r or "city_larger_streets_lined" in r
    assert fired  # a long street with nothing fronting it
    M["commons"] = [{"poly": [[300, 820], [900, 820], [900, 880], [300, 880]], "role": "pasture", "x": 600, "y": 850, "w": 600, "h": 60}]
    r = f(M)
    assert "city_streets_have_buildings" not in r and "city_larger_streets_lined" not in r
