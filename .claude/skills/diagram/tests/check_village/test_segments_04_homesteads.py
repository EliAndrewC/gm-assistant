"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

from l7r.diagram import check_village
from tests.check_village._builders import (
    _EAST_SHADE,
    _PADDY_SQ,
    _SIX,
    _big_grove,
    _bldg,
    _farmhouse,
    _feature_022_manifest,
    _field,
    _grove,
    _harvest,
    _kiln_map,
    _label_map,
    _lbl_city,
    _lbl_town,
    _nuc_grid,
    _nuc_village_M,
    _rural,
    _thin_belt_cluster,
    _well_size_city,
    _yard,
    bldg,
    f,
    house,
    manifest,
    well,
    yard,
)


# ---- the matrix debt register rots loudly ------------------------------------------------------
def test_yards_unshaded_by_neighbors_fires_only_on_a_scripted_map():
    """The check that carries the GM's 2026-08-13 migration decision.

    A neighbor's farmhouse in the 39 ft sun corridor south of a threshing yard fails it - but ONLY
    on a map a generator made (`meta.generated_by`). The whole hand-authored pool breaks this rule
    and is deliberately exempt until each map is converted, so the tag is what turns it on; if that
    gate ever inverts, every legacy map goes red at once and this test says so first."""
    shaded = manifest(
        houses=[house(x=400, y=400), house(x=400, y=500)],
        threshing_yards=[yard(x=400, y=445, of=(400, 400))],
    )
    shaded["meta"]["ftpx"] = 1
    assert "yards_unshaded_by_neighbors" not in f(shaded), "an UNTAGGED (hand-authored) map is exempt by decision"
    shaded["meta"]["generated_by"] = "hamletgen"
    assert "yards_unshaded_by_neighbors" in f(shaded), "a scripted map must be held to it"
    clear = manifest(
        houses=[house(x=400, y=400), house(x=400, y=560)],
        threshing_yards=[yard(x=400, y=445, of=(400, 400))],
    )
    clear["meta"].update(ftpx=1, generated_by="hamletgen")
    assert "yards_unshaded_by_neighbors" not in f(clear), "a yard with its sun must pass"


def test_gardens_present_fires_when_a_farmhouse_has_none():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": []}
    assert "gardens_present" in f(M)


def test_gardens_on_sunny_side_fires_on_a_north_garden():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": [{"x": 520, "y": 455, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}]}  # y=455 is north of 500
    assert "gardens_on_sunny_side" in f(M)


def test_gardens_smaller_than_farmhouse_fires_on_an_oversize_garden():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": [{"x": 545, "y": 500, "w": 60, "h": 40, "rot": 0, "of": [500, 500]}]}  # bigger than the house
    assert "gardens_smaller_than_farmhouse" in f(M)


def test_gardens_clear_of_paddies_fires_on_a_garden_in_a_field():
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "fields": [_field("p", 480, 480, 600, 600)],
        "gardens": [{"x": 530, "y": 530, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
    }  # sits inside the paddy
    assert "gardens_clear_of_paddies" in f(M)


def test_gardens_clear_of_structures_fires_when_a_garden_covers_another_building():
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "buildings": [bldg(545, 500, "shop")],
        "gardens": [{"x": 545, "y": 500, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
    }  # on the shop, not its own house
    assert "gardens_clear_of_structures" in f(M)


def test_gardens_clear_of_sheds_fires_when_a_garden_covers_the_shed():
    # a farm's kura is a recorded annex in M['farm_sheds']; a garden placed on top of it overlaps it.
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}],
        "farm_sheds": [{"x": 500, "y": 476, "w": 20, "h": 9, "rot": 0, "of": [500, 500]}],  # kura on the north wall
        "gardens": [{"x": 500, "y": 478, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
    }  # on the shed
    assert "gardens_clear_of_sheds" in f(M)


def test_gardens_clear_of_channels_fires_when_a_garden_sits_on_a_ditch():
    # a drain ditch runs straight through the garden's footprint - a raised-bed saien in a running ditch
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}],
        "gardens": [{"x": 540, "y": 500, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
        "field_ditches": [{"poly": [[540, 480], [540, 520]], "role": "drain", "w": 6, "field": "f"}],
    }
    assert "gardens_clear_of_channels" in f(M)


def test_farm_sheds_attached_fires_on_a_stranded_kura():
    # a kura recorded far from every farmhouse (a move-procedure stranded it in the open courtyard) must trip
    M = {"meta": {"scale": "village"}, "houses": [{"x": 500, "y": 500, "w": 44, "h": 29, "kind": "plain", "rot": 0}], "farm_sheds": [{"x": 800, "y": 800, "w": 20, "h": 9, "rot": 0, "of": [500, 500]}]}
    assert "farm_sheds_attached" in f(M)


def test_farmhouses_shed_separately_fires_on_a_pair_that_merges_into_one_building():
    # Two steep thatched roofs need their own drip lines and a way between them. Caught by
    # settlement-review on Mizuguchi 2026-08-17: a re-pack flipped one house's rake so a pair
    # diverged instead of running parallel and their raked-corner gap fell to 2.0 ft - two pixels
    # at 1 px = 1 ft, merging into one long building. Nothing measured house-to-house separation
    # at all before this; `no_structure_overlaps` only fires at zero.
    near = {
        "meta": {"scale": "hamlet", "ftpx": 1},
        "houses": [{"x": 500, "y": 500, "w": 46, "h": 28, "kind": "plain", "rot": 0}, {"x": 550, "y": 500, "w": 46, "h": 28, "kind": "plain", "rot": 0}],
    }  # 4 ft of daylight between the walls
    assert "farmhouses_shed_separately" in f(near)


def test_farmhouses_shed_separately_passes_at_an_ordinary_nucleated_spacing():
    # The rule must not fire on a tight-but-honest nucleus: the scripted hamlets sit at 23-29 ft.
    far = {
        "meta": {"scale": "hamlet", "ftpx": 1},
        "houses": [{"x": 500, "y": 500, "w": 46, "h": 28, "kind": "plain", "rot": 0}, {"x": 570, "y": 500, "w": 46, "h": 28, "kind": "plain", "rot": 0}],
    }  # 24 ft apart
    assert "farmhouses_shed_separately" not in f(far)


def test_farmhouses_shed_separately_measures_FEET_not_pixels():
    # The clearance is a physical distance, so it converts through meta.ftpx (FEET per pixel) rather
    # than being a raw pixel literal that would silently mean two different rules at two tiers.
    # The same 6 px wall gap is 6 ft at a hamlet (1 ft/px) - a merge - and 12 ft at a village
    # (2 ft/px), which is honest spacing. So the SAME geometry must fire at one tier and not the other.
    houses = [{"x": 500, "y": 500, "w": 23, "h": 14, "kind": "plain", "rot": 0}, {"x": 529, "y": 500, "w": 23, "h": 14, "kind": "plain", "rot": 0}]
    assert "farmhouses_shed_separately" in f({"meta": {"scale": "hamlet", "ftpx": 1}, "houses": houses}), "6 px = 6 ft at a hamlet: a merge"
    assert "farmhouses_shed_separately" not in f({"meta": {"scale": "village", "ftpx": 2}, "houses": houses}), "the same 6 px = 12 ft at a village: honest spacing"


def test_farmhouses_shed_separately_ignores_a_derelict():
    # A ruin has no roof left to shed, so it is not held to the drip-line rule - the placer skips it too.
    M = {
        "meta": {"scale": "hamlet", "ftpx": 1},
        "houses": [{"x": 500, "y": 500, "w": 46, "h": 28, "kind": "plain", "rot": 0}, {"x": 550, "y": 500, "w": 46, "h": 28, "kind": "abandoned", "rot": 0}],
    }
    assert "farmhouses_shed_separately" not in f(M)


def test_labels_clear_of_other_buildings_fires_on_a_caption_over_a_torii_arch():
    # GM 2026-07-27: an arch is "never covered by the 'temple of X' label" - and the hall's OWN
    # caption was the commonest offender, since caption and sando both want the ground at the front.
    # A torii is a bare [x, y, z] triple, so it needed its own branch in the victim builder; before
    # that it was classified and still checked nothing.
    M = {"meta": {"scale": "city", "ftpx": 3}, "labels": [[480, 552, 620, 566, 5, "Temple of Bishamon"]], "torii": [[500, 560, 1]]}
    assert "labels_clear_of_other_buildings" in f(M)


def test_wells_clear_of_shrine_and_torii_fires_when_a_well_sits_under_the_torii():
    # a well scattered under the torii arch (its disc overlaps the arch box) reads as a wellhead in the gateway
    M = {"meta": {"scale": "village"}, "torii": [[500, 500, 1]], "wells": [{"x": 505, "y": 502, "r": 8}]}
    assert "wells_clear_of_shrine_and_torii" in f(M)


def test_garden_plots_are_quads_fires_on_a_non_quad_poly():
    # a garden whose recorded footprint poly has 3 vertices (a triangle, not a quadrilateral)
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": [{"x": 520, "y": 520, "w": 24, "h": 16, "rot": 0, "of": [500, 500], "poly": [[509, 513], [531, 513], [520, 527]]}]}
    assert "garden_plots_are_quads" in f(M)


def test_garden_plots_are_quads_fires_when_poly_pokes_outside_its_rect():
    # a 4-gon whose first corner (x=560) sits well OUTSIDE the recorded w x h bounds (x in [508, 532]); the
    # jitter only pulls corners INWARD, so an outside vertex means the overlap checks cleared the wrong rect
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 520, "y": 520, "w": 24, "h": 16, "rot": 0, "of": [500, 500], "poly": [[560, 513], [531, 513], [530, 527], [510, 527]]}],
    }
    assert "garden_plots_are_quads" in f(M)


def test_garden_plots_are_quads_passes_on_a_valid_inscribed_quad():
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 520, "y": 520, "w": 24, "h": 16, "rot": 0, "of": [500, 500], "poly": [[509, 513], [531, 512], [530, 527], [510, 528]]}],
    }
    assert "garden_plots_are_quads" not in f(M)


def test_garden_area_within_norms_fires_on_an_oversize_garden():
    # a single bed the size of a field (~60x60 px = 3600 px^2 ~ 1338 m^2 at 2 ft/px), far above a saien's band
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 560, "y": 500, "w": 60, "h": 60, "rot": 0, "of": [500, 500], "poly": [[530, 470], [590, 470], [590, 530], [530, 530]]}],
    }
    assert "garden_area_within_norms" in f(M)


def test_garden_area_within_norms_fires_on_a_tiny_garden():
    # a bed under ~10 m^2 (~27 px^2 at 2 ft/px): a 5x4 poly is ~20 px^2 ~ 7.4 m^2
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 520, "y": 500, "w": 5, "h": 4, "rot": 0, "of": [500, 500], "poly": [[517.5, 498], [522.5, 498], [522.5, 502], [517.5, 502]]}],
    }
    assert "garden_area_within_norms" in f(M)


def test_garden_area_within_norms_passes_and_sums_fragmented_beds():
    # two beds of ONE household, each ~120 px^2 (~45 m^2), summing ~89 m^2 - the fragmented-plot total is in band
    beds = [
        {"x": 512, "y": 500, "w": 12, "h": 10, "rot": 0, "of": [500, 500], "poly": [[506, 495], [518, 495], [518, 505], [506, 505]]},
        {"x": 530, "y": 500, "w": 12, "h": 10, "rot": 0, "of": [500, 500], "poly": [[524, 495], [536, 495], [536, 505], [524, 505]]},
    ]
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "gardens": beds}
    assert "garden_area_within_norms" not in f(M)


def test_groves_on_windward_side_fires_on_a_lee_grove():
    # default windward NW; a grove on the SE (lee/sunny) side of its house is backwards
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "groves": [_grove(540, 540, 500, 500)]}  # SE of the house, not the windward NW
    assert "groves_on_windward_side" in f(M)


def test_groves_on_windward_side_respects_meta_windward():
    # with the wind keyed to the NE, a grove on the SW is on the lee side and fires
    M = {"meta": {"scale": "village", "windward": "NE"}, "houses": [_farmhouse(500, 500)], "groves": [_grove(460, 540, 500, 500)]}  # SW, but windward is NE
    assert "groves_on_windward_side" in f(M)


def test_groves_on_windward_side_passes_on_a_nw_grove():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "groves": [_grove(465, 470, 500, 500)]}  # NW of the house - windward
    assert "groves_on_windward_side" not in f(M)


def test_groves_clear_of_paddies_fires_on_a_grove_in_a_field():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "fields": [_field("p", 440, 440, 600, 600)], "groves": [_grove(465, 470, 500, 500)]}  # NW corner sits inside the paddy
    assert "groves_clear_of_paddies" in f(M)


def test_groves_clear_of_structures_fires_when_a_grove_covers_another_building():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(500, 500)], "buildings": [bldg(460, 470, "shop")], "groves": [_grove(460, 470, 500, 500)]}  # on the shop, not its own house
    assert "groves_clear_of_structures" in f(M)


def test_groves_where_possible_fires_when_a_clear_windward_farm_has_none():
    # 12 farmhouses with open windward sides (no fields/structs/corridors) and no groves -> the generator
    # would have placed groves; a grove-less farm with clear windward room is flagged
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(300 + 60 * i, 400) for i in range(12)], "groves": []}
    assert "groves_where_possible" in f(M)


def test_groves_where_possible_passes_when_windward_is_blocked():
    # the same farms, but a field hugs every windward (N + W) side -> no room -> no grove required
    houses = [_farmhouse(300 + 60 * i, 400) for i in range(12)]
    fields = [_field(f"f{i}", 280 + 60 * i, 330, 340 + 60 * i, 395) for i in range(12)]  # field just N of each house
    M = {"meta": {"scale": "village", "windward": "N"}, "houses": houses, "fields": fields, "groves": []}
    assert "groves_where_possible" not in f(M)


def test_groves_where_possible_tolerates_a_yard_strip_shaded_windward_side():
    """A farm whose windward clump seat lands on a threshing yard's DRYING STRIP (the 11px band
    below the yard - which the avoid center-box test deliberately cannot see) is legitimately
    grove-less. Deterministic cover for the yard-strip rejection in clump_clear: before feature
    024's per-check split this branch was reached only incidentally via the mega-segment's full
    replay (same shape as the feature-022 manor-walls precedent)."""
    houses = [_farmhouse(300 + 60 * i, 400) for i in range(12)]
    dm = 13 * 46 / 44.0  # minimal-clump depth for the 46px farmhouse (mirrors min_clump)
    cy = 400 - (28 / 2 + dm / 2 + 1.5)  # the windward-"N" clump seat's center
    # yard 30px above the seat: outside the avoid box (30 >= (dm+26)/2+7) but its strip center
    # (yd.y + h/2 + 11) sits 6px from the seat, well inside the strip test
    yards = [yard(300 + 60 * i, cy - 30, of=(300 + 60 * i, 400)) for i in range(12)]
    M = {"meta": {"scale": "village", "windward": "N"}, "houses": houses, "threshing_yards": yards, "groves": []}
    assert "groves_where_possible" not in f(M)


def test_groves_where_possible_skipped_for_a_nucleated_village():
    # a NUCLEATED village shelters behind the COMMUNAL windbreak, not per-house groves, so bare farms with
    # clear windward room must NOT fire groves_where_possible - though the SAME setup DOES fire when dispersed
    houses = [_farmhouse(300 + 60 * i, 400) for i in range(12)]
    assert "groves_where_possible" in f({"meta": {"scale": "village"}, "houses": houses, "groves": []})
    assert "groves_where_possible" not in f({"meta": {"scale": "village", "nucleated": True}, "houses": houses, "groves": []})


def test_village_windbreak_present_fires_when_a_nucleated_village_has_none():
    assert "village_windbreak_present" in f(_nuc_village_M(_nuc_grid(), []))


def test_village_windbreak_present_passes_with_a_back_grove_on_the_windward_side():
    houses = _nuc_grid()
    ccx = sum(h["x"] for h in houses) / len(houses)
    ccy = sum(h["y"] for h in houses) / len(houses)
    wb = [{"x": ccx - 150, "y": ccy - 150, "w": 72, "h": 300, "rot": 0, "role": "windbreak"}]  # NW of the centroid
    fails = f(_nuc_village_M(houses, wb))
    assert "village_windbreak_present" not in fails and "village_windbreak_on_windward_side" not in fails


def test_village_windbreak_on_windward_side_fires_on_a_lee_belt():
    houses = _nuc_grid()
    ccx = sum(h["x"] for h in houses) / len(houses)
    ccy = sum(h["y"] for h in houses) / len(houses)
    wb = [{"x": ccx + 150, "y": ccy + 150, "w": 72, "h": 300, "rot": 0, "role": "windbreak"}]  # SE = the sunny lee
    assert "village_windbreak_on_windward_side" in f(_nuc_village_M(houses, wb))


def test_village_groves_clear_of_paddies_fires_on_a_grove_in_a_field():
    # no recorded clumps -> the bbox center is all there is to test (older maps)
    M = _nuc_village_M(_nuc_grid(), [{"x": 600, "y": 600, "w": 40, "h": 40, "rot": 0, "role": "copse"}], fields=[_field("p", 540, 540, 700, 700)])
    assert "village_groves_clear_of_paddies" in f(M)


def test_village_groves_clear_of_paddies_tests_the_trees_not_the_bounding_box():
    # a crescent belt hugging the field edge can have its BOX center over the crop while every tree in it
    # stands on dry ground (Ueda's 87-clump back belt) - that must pass ...
    field = [_field("p", 540, 540, 700, 700)]
    crescent = {"x": 600, "y": 600, "w": 200, "h": 200, "rot": 0, "role": "windbreak", "r": 14, "clumps": [[480, 520], [500, 480], [520, 460]]}
    assert "village_groves_clear_of_paddies" not in f(_nuc_village_M(_nuc_grid(), [crescent], fields=field))
    # ... while a single tree actually standing in the paddy fires, even with the box center on dry ground
    intruder = {"x": 300, "y": 300, "w": 200, "h": 200, "rot": 0, "role": "copse", "r": 11, "clumps": [[260, 260], [600, 600]]}
    assert "village_groves_clear_of_paddies" in f(_nuc_village_M(_nuc_grid(), [intruder], fields=field))


def test_gardens_clear_of_groves_fires_when_a_garden_is_buried():
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "gardens": [{"x": 540, "y": 500, "w": 24, "h": 16, "rot": 0, "of": [500, 500]}],
        "groves": [_grove(540, 500, 700, 700)],
    }  # grove sits squarely on the garden
    assert "gardens_clear_of_groves" in f(M)


def test_groves_are_substantial_fires_on_tiny_groves():
    houses = [_farmhouse(300 + 60 * i, 300) for i in range(6)]
    groves = [_grove(285 + 60 * i, 270, 300 + 60 * i, 300, w=10, h=10) for i in range(6)]  # clumps, ~0.08x the house
    assert "groves_are_substantial" in f({"meta": {"scale": "village"}, "houses": houses, "groves": groves})


def test_groves_are_substantial_passes_with_belts():
    houses = [_farmhouse(300 + 60 * i, 300) for i in range(6)]
    groves = [_big_grove(300 + 60 * i, 300, 300 + 60 * i, 300) for i in range(6)]
    assert "groves_are_substantial" not in f({"meta": {"scale": "village"}, "houses": houses, "groves": groves})


def test_yards_unshaded_by_groves_fires():
    # a grove in the strip directly south of a threshing yard would shade its drying ground
    M = {
        "meta": {"scale": "village"},
        "houses": [_farmhouse(500, 500)],
        "threshing_yards": [{"x": 500, "y": 540, "w": 32, "h": 20, "rot": 0, "of": [500, 500]}],
        "groves": [_grove(500, 562, 700, 700)],
    }  # grove just south of the yard (its south edge ~550)
    assert "yards_unshaded_by_groves" in f(M)


def test_village_trees_unshade_fires_when_a_clump_is_south_of_a_yard():
    M = {
        "meta": {"scale": "village"},
        "threshing_yards": [{"x": 300, "y": 400, "w": 40, "h": 24, "rot": 0, "of": [300, 380]}],
        "village_groves": [{"role": "copse", "r": 11, "clumps": [[300, 430]], "poly": [[280, 415], [320, 415], [320, 445], [280, 445]]}],
    }  # clump S of the yard
    assert "village_trees_unshade_yards_and_gardens" in f(M)


def test_village_trees_unshade_fires_when_a_clump_is_south_of_a_garden():
    M = {
        "meta": {"scale": "village"},
        "gardens": [{"x": 300, "y": 400, "w": 30, "h": 20, "rot": 0, "of": [300, 380]}],
        "village_groves": [{"role": "copse", "r": 11, "clumps": [[300, 425]], "poly": [[280, 410], [320, 410], [320, 440], [280, 440]]}],
    }  # clump S of the garden
    assert "village_trees_unshade_yards_and_gardens" in f(M)


def test_village_trees_unshade_passes_when_the_clump_is_north():
    M = {
        "meta": {"scale": "village"},
        "threshing_yards": [{"x": 300, "y": 400, "w": 40, "h": 24, "rot": 0, "of": [300, 380]}],
        "village_groves": [
            {
                "role": "copse",
                "r": 11,
                "clumps": [[300, 300]],  # NORTH of the yard
                "poly": [[280, 285], [320, 285], [320, 315], [280, 315]],
            }
        ],
    }
    assert "village_trees_unshade_yards_and_gardens" not in f(M)


# --- labels_within_image (a label must not run off the edge of the rendered frame) ---
def test_labels_within_image_fires_when_a_label_runs_off_the_edge():
    # the default canvas is 1820x1180; this label pokes past the right edge
    M = {"meta": {}, "labels": [[1750, 500, 1900, 512, 1, "off the right edge"]]}
    assert "labels_within_image" in f(M)


def test_labels_within_image_passes_when_inside():
    M = {"meta": {}, "labels": [[100, 100, 300, 112, 1, "comfortably inside"]]}
    assert "labels_within_image" not in f(M)


def test_margins_form_continuous_ring_passes_when_the_frame_is_clothed():
    # one commons band + the field cover the whole (small) view - only feathered seams left
    M = {
        "meta": {"scale": "village", "view": [0, 0, 400, 300]},
        "fields": [_field("p", 0, 0, 400, 150)],
        "commons": [{"poly": [[0, 140], [400, 140], [400, 300], [0, 300]], "role": "grazing"}],
    }
    assert "margins_form_continuous_ring" not in f(M)


def test_margins_form_continuous_ring_fires_on_bare_open_plain():
    # the real Ueda defect in miniature: the ring bands sit OFF-FRAME (west of the cropped view),
    # so the framed map is mostly bare open tan around a small field
    M = {
        "meta": {"scale": "village", "view": [500, 0, 400, 300]},
        "fields": [_field("p", 500, 0, 650, 150)],
        "commons": [{"poly": [[0, 0], [480, 0], [480, 300], [0, 300]], "role": "grazing"}],
    }
    assert "margins_form_continuous_ring" in f(M)


def test_margins_form_continuous_ring_ignores_town_and_city_sheets():
    # urban sheets cover the ground with streets/wards/walls these feature sets do not model -
    # the satoyama-ring doctrine is village/hamlet scope only
    M = {"meta": {"scale": "town", "view": [0, 0, 400, 300]}}
    assert "margins_form_continuous_ring" not in f(M)


def test_scatter_respects_swept_clearings_fires_on_cover_before_the_collar():
    # the real Ueda graveyard defect in miniature: the grazing band (seq 1) drew BEFORE the grave
    # collar was registered (clearing seq 1 = one cover already drawn), so tufts landed on swept ground
    M = {
        "meta": {"scale": "village"},
        "commons": [{"poly": [[50, 50], [400, 50], [400, 400], [50, 400]], "role": "grazing", "seq": 1}],
        "clearings": [{"poly": [[100, 100], [200, 100], [200, 200], [100, 200]], "seq": 1}],
    }
    assert "scatter_respects_swept_clearings" in f(M)


def test_scatter_respects_swept_clearings_passes_when_the_ground_was_reserved():
    # the documented reserve_clearing pattern: the collar is reserved (seq 0, before any cover), the
    # band draws (seq 1, skips it), then the cemetery registers its own duplicate collar late (seq 1) -
    # harmless, because a pre-cover guard clearing already protected every point of it
    M = {
        "meta": {"scale": "village"},
        "commons": [{"poly": [[50, 50], [400, 50], [400, 400], [50, 400]], "role": "grazing", "seq": 1}],
        "clearings": [
            {"poly": [[100, 100], [200, 100], [200, 200], [100, 200]], "seq": 0},
            {"poly": [[100, 100], [200, 100], [200, 200], [100, 200]], "seq": 1},
        ],
    }
    assert "scatter_respects_swept_clearings" not in f(M)


def test_scatter_respects_swept_clearings_passes_when_the_cover_draws_after():
    # normal order: clearing registered first (seq 0), the band draws after (seq 1) and skips it
    M = {
        "meta": {"scale": "village"},
        "commons": [{"poly": [[50, 50], [400, 50], [400, 400], [50, 400]], "role": "grazing", "seq": 1}],
        "clearings": [{"poly": [[100, 100], [200, 100], [200, 200], [100, 200]], "seq": 0}],
    }
    assert "scatter_respects_swept_clearings" not in f(M)


def test_harvest_and_garden_checks_cover_the_headman():
    # the headman is a FARMSTEAD, not an exception to farmstead anatomy (GM 2026-07-21, caught on
    # Hikari no Sato): the old role=="headman" carve-out in occ_h existed only because the dispersed
    # headman() predated the homestead bundle and drew a lone house - a headman with no yard and no
    # garden now fires BOTH universal checks
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 46, "h": 28, "rot": 0, "kind": "plain", "role": "headman"}],
    }
    fails = f(M)
    assert "harvest_yards_present" in fails
    assert "gardens_present" in fails


def test_wells_sized_to_population_bands():
    # the Rokugan prosperity liberty, banded (GM 2026-07-21): villages 8-26 hh/well, hamlets 2-20;
    # shrine temizu wells are excluded from the count
    base = {"meta": {"scale": "village", "households": 70}}
    M = {**base, "wells": [{"x": 100 * i, "y": 100, "r": 8, "shrine": False} for i in range(5)]}
    assert "wells_sized_to_population" not in f(M)  # 14 hh/well - in band
    M = {**base, "wells": [{"x": 100, "y": 100, "r": 8, "shrine": False}]}
    assert "wells_sized_to_population" in f(M)  # 70 hh/well - parched
    M = {**base, "wells": [{"x": 60 * i, "y": 100, "r": 8, "shrine": False} for i in range(12)]}
    assert "wells_sized_to_population" in f(M)  # 5.8 hh/well - urban-tenement density in a village
    M = {**base, "wells": [{"x": 100 * i, "y": 100, "r": 8, "shrine": False} for i in range(5)] + [{"x": 900, "y": 900, "r": 8, "shrine": True}] * 9}
    assert "wells_sized_to_population" not in f(M)  # shrine wells do not tip the band
    H = {"meta": {"scale": "hamlet", "households": 16}, "wells": [{"x": 100 * i, "y": 100, "r": 8, "shrine": False} for i in range(6)]}
    assert "wells_sized_to_population" not in f(H)  # 2.7 hh/well - per-farmstead hamlet pattern, in band
    H["wells"] = []
    assert "wells_sized_to_population" in f(H)  # a settlement with no draw-well at all


def test_lanes_clear_of_dry_plots_fires_on_a_path_through_the_crop():
    # Hikari's defect in miniature (GM 2026-07-21): a lane crossing a dry plot's interior fires; a
    # lane running along the plot's edge (a path hugs the field margin by design) passes
    plot = {"poly": [[300, 300], [400, 300], [400, 400], [300, 400]], "crop": "barley", "theta": 0}
    M = {"meta": {"scale": "village"}, "dry_plots": [plot], "lanes": [{"pts": [[250, 350], [450, 350]], "width": 5}]}
    assert "lanes_clear_of_dry_plots" in f(M)
    M["lanes"] = [{"pts": [[250, 300], [450, 300]], "width": 5}]  # along the top edge - touching, not through
    assert "lanes_clear_of_dry_plots" not in f(M)
    M["lanes"] = [{"pts": [[250, 250], [450, 250]], "width": 5}]  # clear of the plot entirely
    assert "lanes_clear_of_dry_plots" not in f(M)


def test_labels_within_image_uses_the_cropped_view():
    # with a crop set, the frame is the viewBox - a label inside the full canvas but WEST of the crop
    # (a city map crops tight to the walls) is clipped and fires
    M = {"meta": {"view": [658, 448, 1884, 1764]}, "labels": [[300, 690, 500, 702, 1, "west of the crop"]]}
    assert "labels_within_image" in f(M)


def test_labels_clear_of_other_buildings_fires_when_label_over_a_foreign_building():
    # a "flophouse" label spilling onto a merchant house next door
    assert "labels_clear_of_other_buildings" in f(_lbl_city(buildings=[_bldg("merchant_house")]))


def test_labels_clear_of_other_buildings_fires_when_guard_label_over_a_flophouse():
    M = _lbl_city(labels=[[470, 490, 560, 510, 1, "gate guard house + inspection"]], flophouses=[{"x": 500, "y": 500, "w": 90, "h": 42, "rot": 0}])
    assert "labels_clear_of_other_buildings" in f(M)


def test_labels_clear_of_other_buildings_passes_over_its_own_building():
    assert "labels_clear_of_other_buildings" not in f(_lbl_city(flophouses=[{"x": 500, "y": 500, "w": 90, "h": 42, "rot": 0}]))


def test_labels_clear_of_other_buildings_passes_over_a_fronting_shop():
    # a market/zone label may clip a street-fronting shop (shops line every quarter)
    M = _lbl_city(labels=[[480, 490, 520, 510, 1, "gate market"]], buildings=[_bldg("shop")])
    assert "labels_clear_of_other_buildings" not in f(M)


def test_labels_clear_of_other_buildings_passes_for_a_zone_label_over_its_cluster():
    M = _lbl_city(labels=[[480, 490, 520, 510, 1, "samurai neighborhood"]], buildings=[_bldg("samurai", w=56, h=40)])
    assert "labels_clear_of_other_buildings" not in f(M)


def test_labels_clear_town_monastery_label_over_graveyard_fires():
    M = _lbl_town("Monastery of Bishamon", cemeteries=[{"x": 500, "y": 500, "w": 80, "h": 50, "rot": 0, "parish": True}])
    assert "labels_clear_of_other_buildings" in f(M)


def test_labels_clear_town_graveyard_label_over_temple_fires():
    M = _lbl_town("graveyard", religious=[{"kind": "monastery", "x": 500, "y": 500, "w": 80, "h": 50, "label": "M"}])
    assert "labels_clear_of_other_buildings" in f(M)


def test_labels_clear_town_funerary_label_over_funerary_passes():
    # the funerary structures cluster, so a funerary label may cover any of them
    M = _lbl_town("cremation ground", cemeteries=[{"x": 500, "y": 500, "w": 80, "h": 50, "rot": 0, "parish": True}])
    assert "labels_clear_of_other_buildings" not in f(M)


def test_labels_clear_town_street_label_over_merchant_passes():
    # a street/road label runs along its frontage, so it may clip the storefronts it lines
    M = _lbl_town("main street", buildings=[_bldg("merchant", w=60, h=40)])
    assert "labels_clear_of_other_buildings" not in f(M)


def test_settlement_has_wells_fires_when_too_few():
    # 40 farm households, no wells at all
    assert "settlement_has_wells" in f(_rural("village", [(300 + i * 10, 300) for i in range(40)], []))


def test_settlement_dwellings_watered_fires_when_a_house_is_dry():
    # one house 600px from the only well, with no irrigation nearby
    assert "settlement_dwellings_watered" in f(_rural("village", [(300, 300), (300, 900)], [(300, 300)]))


def test_settlement_dwellings_watered_passes_via_irrigation():
    # the far house has no well within reach but sits beside a stream
    M = _rural("hamlet", [(300, 900)], [(300, 300)], streams=[{"poly": [[200, 880], [400, 880]], "frm": None, "to": None, "w": 9}])
    assert "settlement_dwellings_watered" not in f(M)


def test_remote_shrine_has_own_well_fires_when_a_set_apart_shrine_has_none():
    # the shrine sits far from the houses AND far from the one well -> it must keep its OWN well close by
    M = _rural("village", [(300, 300)], [(310, 305)], religious=[{"x": 1200, "y": 1200, "w": 30, "h": 24, "kind": "shrine"}])
    assert "remote_shrine_has_own_well" in f(M)


def test_remote_shrine_has_own_well_passes_with_a_well_close_by():
    M = _rural(
        "village",
        [(300, 300)],
        [(310, 305), (1210, 1205)],  # a second well right beside the remote shrine
        religious=[{"x": 1200, "y": 1200, "w": 30, "h": 24, "kind": "shrine"}],
    )
    assert "remote_shrine_has_own_well" not in f(M)


def test_remote_shrine_own_well_not_required_when_a_ditch_is_near():
    # a ditch/pond is NOT an ablution source - a set-apart shrine still needs its own WELL, so a nearby ditch does not save it
    M = _rural(
        "village",
        [(300, 300)],
        [(310, 305)],
        religious=[{"x": 1200, "y": 1200, "w": 30, "h": 24, "kind": "shrine"}],
        field_ditches=[{"poly": [[1180, 1180], [1220, 1220]], "w": 5, "role": "main", "field": "p"}],
    )
    assert "remote_shrine_has_own_well" in f(M)  # the ditch by the shrine does not count


def test_remote_shrine_among_the_houses_is_exempt():
    # a shrine near the dwellings shares the village wells - no own well required
    M = _rural("village", [(300, 300)], [(310, 305)], religious=[{"x": 360, "y": 340, "w": 30, "h": 24, "kind": "shrine"}])
    assert "remote_shrine_has_own_well" not in f(M)


def test_wells_clear_of_paddies_fires_on_a_well_in_the_fan():
    # GM 2026-07-27: "wells on dry crops are okay, but not in rice paddies, surely". A paddy is a
    # puddled, bunded basin held under standing water - a wellhead drawn in one stands in the water
    # it is an alternative to. Nothing saw it before: _well_ground_clear refused a stream, channel,
    # ditch, canal, pond and DRY plot but never a wet one, and the overlap matrix classes `fields`
    # PADDY_RECONSTRUCTED (permissive) because a plot polygon is not stored. The real instance is
    # frozen in pool/regressions/ (Tango's well laid against a drawn basin of the fe1 fan).
    basin = [[600, 600], [900, 600], [900, 900], [600, 900]]
    paddy = {"name": "f1", "kind": "paddy", "outline": [[400, 400], [900, 400], [900, 900], [400, 900]], "bbox": [400, 400, 900, 900], "plot_polys": [basin]}
    inside = manifest(fields=[paddy], wells=[well(750, 750)], houses=[house(750, 950)])
    assert "wells_clear_of_paddies" in f(inside)
    outside = manifest(fields=[paddy], wells=[well(750, 990)], houses=[house(750, 950)])
    assert "wells_clear_of_paddies" not in f(outside)
    # the DRAWN head may not lap a basin either - the same strictness as the dry-plot rule
    grazing = manifest(fields=[paddy], wells=[well(750, 594, vr=12)], houses=[house(750, 950)])
    assert "wells_clear_of_paddies" in f(grazing)
    # ...but the fan's unplanted RIM SLACK stays legal: inside the smoothed envelope, clear of every
    # drawn basin. That margin is where farm_wells seats the well of a steading boxed in by crop, and
    # reading the envelope as water instead is what left Tango's east pair with no seat at all
    slack = manifest(fields=[paddy], wells=[well(450, 450)], houses=[house(450, 950)])
    assert "wells_clear_of_paddies" not in f(slack)
    # a field recording NO drawn basins falls back to its outline, so the rural tiers - which record
    # none - are not silently exempt from a rule the cities are held to
    unplotted = manifest(fields=[{k: v for k, v in paddy.items() if k != "plot_polys"}], wells=[well(450, 450)], houses=[house(450, 950)])
    assert "wells_clear_of_paddies" in f(unplotted)
    # ...and a DRY plot is expressly allowed: this rule is about standing water, not about crops
    dry = manifest(dry_plots=[{"poly": [[400, 400], [900, 400], [900, 900], [400, 900]], "crop": "barley"}], wells=[well(650, 650)], houses=[house(650, 940)])
    assert "wells_clear_of_paddies" not in f(dry)


def test_wells_among_dwellings_fires_on_a_stray_well():
    # a well far out in open country, no house beside it
    assert "wells_among_dwellings" in f(_rural("village", [(300, 300)], [(900, 900)]))


def test_wells_among_dwellings_passes_when_beside_a_house():
    assert "wells_among_dwellings" not in f(_rural("village", [(300, 300)], [(340, 300)]))


def test_wells_sized_to_buildings_fires_when_too_small():
    # a 10px wellhead (the dense-city size) beside 44px village farmhouses - far too small
    assert "wells_sized_to_buildings" in f(_well_size_city(5.0))


def test_wells_sized_to_buildings_passes_when_proportional():
    # scaled to the village grain (~24px), about half a farmhouse
    assert "wells_sized_to_buildings" not in f(_well_size_city(11.9))


def test_harvest_yards_present_fires_when_any_farmhouse_lacks_one():
    # 5 of 6 yards - even one farmhouse without a yard fails (the work yard was universal)
    assert "harvest_yards_present" in f(_harvest(_SIX, [_yard(h) for h in _SIX[:5]]))


def test_harvest_yards_present_passes_when_every_farmhouse_has_one():
    assert "harvest_yards_present" not in f(_harvest(_SIX, [_yard(h) for h in _SIX]))


def test_harvest_yards_smaller_than_farmhouse_fires_when_oversize():
    assert "harvest_yards_smaller_than_farmhouse" in f(_harvest([(300, 300)], [_yard((300, 300), w=60, h=44)]))


def test_harvest_yards_smaller_than_farmhouse_passes_when_small():
    assert "harvest_yards_smaller_than_farmhouse" not in f(_harvest([(300, 300)], [_yard((300, 300))]))


def test_harvest_yards_on_sunny_side_fires_when_north_of_house():
    # +y is south; a yard ABOVE its house center sits on the shady north/back side
    y = {"x": 300, "y": 260, "w": 32, "h": 20, "rot": 0, "of": [300, 300]}
    assert "harvest_yards_on_sunny_side" in f(_harvest([(300, 300)], [y]))


def test_harvest_yards_on_sunny_side_passes_when_south_of_house():
    y = {"x": 300, "y": 340, "w": 32, "h": 20, "rot": 0, "of": [300, 300]}
    assert "harvest_yards_on_sunny_side" not in f(_harvest([(300, 300)], [y]))


def test_harvest_yards_clear_of_paddies_fires_when_in_a_paddy():
    # the yard footprint sits inside the field (400,400)-(600,600) - a dry floor in the flooded paddy
    y = {"x": 500, "y": 500, "w": 32, "h": 20, "rot": 0, "of": [460, 460]}
    M = _harvest([(460, 460)], [y], fields=[{"name": "a", "kind": "paddy", "bbox": [400, 400, 600, 600], "outline": _PADDY_SQ}])
    assert "harvest_yards_clear_of_paddies" in f(M)


def test_harvest_yards_clear_of_paddies_passes_when_clear():
    y = {"x": 720, "y": 300, "w": 32, "h": 20, "rot": 0, "of": [676, 300]}
    M = _harvest([(676, 300)], [y], fields=[{"name": "a", "kind": "paddy", "bbox": [400, 400, 600, 600], "outline": _PADDY_SQ}])
    assert "harvest_yards_clear_of_paddies" not in f(M)


def test_harvest_yards_clear_of_structures_fires_on_another_building():
    # the yard (344,300) overlaps a shop - only its OWN farmhouse (300,300) may underlie it
    M = _harvest([(300, 300)], [_yard((300, 300))])
    M["buildings"] = [{"x": 352, "y": 300, "w": 44, "h": 30, "rot": 0, "kind": "shop"}]
    assert "harvest_yards_clear_of_structures" in f(M)


def test_harvest_yards_clear_of_structures_passes_when_only_on_its_own_house():
    M = _harvest([(300, 300)], [_yard((300, 300))])
    M["buildings"] = [{"x": 700, "y": 700, "w": 44, "h": 30, "rot": 0, "kind": "shop"}]  # far away
    assert "harvest_yards_clear_of_structures" not in f(M)


# ---- grove_clumps_clear_of_structures: a tree blob may abut but not overlap a farmstead ----
def test_grove_clumps_clear_of_structures_fires_on_a_clump_over_a_house():
    on = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 40, "h": 30, "rot": 0, "kind": "plain"}],
        "village_groves": [{"role": "copse", "r": 11, "clumps": [[515, 505]]}],
    }  # blob center inside the house
    assert "grove_clumps_clear_of_structures" in f(on)
    beside = {**on, "village_groves": [{"role": "copse", "r": 11, "clumps": [[560, 505]]}]}  # abuts, off the wall
    assert "grove_clumps_clear_of_structures" not in f(beside)


def test_grove_clumps_clear_of_structures_covers_a_garden_and_a_shed():
    # the check sweeps the whole homestead, not just houses - a clump on a garden or a farm shed also fires
    gd = {"meta": {"scale": "village"}, "gardens": [{"x": 500, "y": 500, "w": 20, "h": 18, "rot": 0, "of": [500, 470]}], "village_groves": [{"role": "copse", "r": 11, "clumps": [[500, 500]]}]}
    assert "grove_clumps_clear_of_structures" in f(gd)
    sh = {"meta": {"scale": "village"}, "farm_sheds": [{"x": 500, "y": 500, "w": 24, "h": 20, "rot": 0, "of": [470, 500]}], "village_groves": [{"role": "copse", "r": 11, "clumps": [[500, 500]]}]}
    assert "grove_clumps_clear_of_structures" in f(sh)


def test_gardens_unshaded_from_east_fires_when_avoidable():
    assert "gardens_unshaded_from_east" in f(_EAST_SHADE)  # clear ground to the S -> the garden should have moved


def test_gardens_unshaded_from_east_exempts_a_south_boxed_garden():
    # each obstacle type to the S boxes the garden in -> unavoidable -> exempt (exercises every _bed_clear branch)
    house_s = {**_EAST_SHADE, "houses": _EAST_SHADE["houses"] + [{"x": 320, "y": 325, "w": 44, "h": 44, "rot": 0, "kind": "plain"}]}
    assert "gardens_unshaded_from_east" not in f(house_s)
    yard_s = {**_EAST_SHADE, "threshing_yards": [{"x": 320, "y": 325, "w": 44, "h": 44, "rot": 0, "of": [999, 999]}]}
    assert "gardens_unshaded_from_east" not in f(yard_s)
    lane_s = {**_EAST_SHADE, "lanes": [{"pts": [[280, 325], [360, 325]], "w": 40}]}  # a wide lane bars the whole shift band
    assert "gardens_unshaded_from_east" not in f(lane_s)
    water_s = {**_EAST_SHADE, "channels": [{"poly": [[280, 325], [360, 325]], "frm": {"kind": "offmap"}, "to": {"kind": "offmap"}}]}
    assert "gardens_unshaded_from_east" not in f(water_s)
    hill_s = {**_EAST_SHADE, "hill": [320, 325, 30, 30]}
    assert "gardens_unshaded_from_east" not in f(hill_s)


def test_gardens_unshaded_from_east_skips_when_no_per_house_groves():
    # the rule is scoped to villages whose farms carry per-house windward groves; with none, it does not run
    assert "gardens_unshaded_from_east" not in f({k: v for k, v in _EAST_SHADE.items() if k != "groves"})


def test_wells_clear_of_trees_fires_on_grove_forest_woodland_grect_but_passes_when_clear():
    # a wellhead is a clean draw-point: it must not sit under ANY tree - the fengshui grove clumps, the
    # per-house grove rects, a forest, or a coppice-woodland patch. Each type fires; a well on open ground does not.
    base = {"meta": {"scale": "village"}, "houses": [bldg(300, 300, "laborer")]}
    well = {"x": 500, "y": 500, "r": 8, "vr": 12}
    on_grove = {**base, "wells": [well], "village_groves": [{"role": "windbreak", "x": 505, "y": 505, "r": 14, "clumps": [[505, 505]]}]}
    assert "wells_clear_of_trees" in f(on_grove)
    on_forest = {**base, "wells": [well], "forest": [[400, 400], [600, 400], [600, 600], [400, 600]]}
    assert "wells_clear_of_trees" in f(on_forest)
    on_wood = {**base, "wells": [well], "commons": [{"x": 500, "y": 500, "role": "woodland", "poly": [[440, 440], [560, 440], [560, 560], [440, 560]]}]}
    assert "wells_clear_of_trees" in f(on_wood)
    on_grect = {**base, "wells": [well], "groves": [{"x": 505, "y": 505, "w": 40, "h": 30, "of": [300, 300], "face": [0, -1]}]}
    assert "wells_clear_of_trees" in f(on_grect)
    clear = {**base, "wells": [well], "village_groves": [{"role": "windbreak", "x": 900, "y": 900, "r": 14, "clumps": [[900, 900]]}]}
    assert "wells_clear_of_trees" not in f(clear)


def test_wells_clear_of_trees_fires_on_a_drawn_crown_over_the_wellhead():
    # the reserved-area tests above are coarse (where trees MAY stand); tree_crowns is where they DO.
    # A crown drawn onto the wellhead fires even with no grove/forest record anywhere near it.
    base = manifest(houses=[bldg(300, 300, "laborer")])
    wl = well(500, 500)
    assert "wells_clear_of_trees" in f({**base, "wells": [wl], "tree_crowns": [508, 495, 9]})
    assert "wells_clear_of_trees" not in f({**base, "wells": [wl], "tree_crowns": [540, 495, 9]})


# ---- gardens_unshaded_from_east: a garden truly boxed in to the SOUTH by a bog is EXEMPT ----
# The east-shade relaxer only fires when a small SOUTHWARD nudge into OPEN ground would clear
# the morning-sun shadow. When every candidate shift lands the garden bed on a bog/marsh (or a
# field outline), no clear shift exists, so the garden is exempt and the check must NOT fire.
# This pins the field-outline / bog clause of the internal _bed_clear helper.
def test_gardens_unshaded_from_east_exempt_when_south_shift_blocked_by_a_bog():
    M = {
        "meta": {"scale": "village"},
        "houses": [{"x": 500, "y": 500, "w": 40, "h": 30, "rot": 0, "kind": "plain"}],
        "gardens": [{"x": 500, "y": 500, "w": 30, "h": 30, "of": [500, 500]}],
        "groves": [{"x": 545, "y": 500, "w": 40, "h": 30, "of": [999, 999]}],  # neighbor grove hard against the garden's east
        "marshes": [{"poly": [[480, 510], [520, 510], [520, 600], [480, 600]]}],  # bog fills the whole southward corridor
    }
    assert "gardens_unshaded_from_east" not in f(M)


def test_village_windbreak_embraces_cluster_fires_on_far_corner_masses_only():
    # a substantial belt exists but stands 400px from the nearest farmhouse - decoration, not a wall
    houses = [{"x": 500 + i * 30, "y": 500, "w": 23, "h": 14, "kind": "plain", "rot": 0} for i in range(12)]
    far = {"x": 900, "y": 100, "w": 120, "h": 60, "role": "windbreak", "clumps": [[880 + j * 6, 100] for j in range(14)]}
    M = {"meta": {"scale": "village", "nucleated": True}, "houses": houses, "village_groves": [far]}
    assert "village_windbreak_embraces_cluster" in f(M)


def test_village_windbreak_embraces_cluster_passes_when_the_belt_nestles():
    houses = [{"x": 500 + i * 30, "y": 500, "w": 23, "h": 14, "kind": "plain", "rot": 0} for i in range(12)]
    belt = {"x": 590, "y": 420, "w": 300, "h": 50, "role": "windbreak", "clumps": [[470 + j * 22, 425] for j in range(14)]}
    M = {"meta": {"scale": "village", "nucleated": True}, "houses": houses, "village_groves": [belt]}
    assert "village_windbreak_embraces_cluster" not in f(M)


def test_village_windbreak_scales_with_cluster_fires_on_a_belt_too_thin_for_the_cluster():
    M = _thin_belt_cluster()
    fails = f(M)
    assert "village_windbreak_scales_with_cluster" in fails and "village_windbreak_embraces_cluster" not in fails


def test_village_windbreak_scales_with_cluster_counts_per_house_groves():
    # a map that ALSO groves its farmhouses (Hikari-no-Sato does both) banks those yashikirin footprints
    M = _thin_belt_cluster(groves=[_grove(500 + i * 30 - 18, 480, 500 + i * 30, 500, w=40, h=40) for i in range(12)])
    assert "village_windbreak_scales_with_cluster" not in f(M)


def test_village_windbreak_forest_exempts_only_when_it_shelters_the_cluster():
    # a REAL FOREST standing at the cluster's windward (NW) back, within nestling reach, IS the wind wall
    near = _thin_belt_cluster(forest=[[400, 360], [420, 420], [400, 470]])
    assert "village_windbreak_scales_with_cluster" not in f(near)
    # ... but a wood on the LEE side, half a map away, shelters nothing - no exemption (Moritono's Shirin
    # Forest, 1,089 ft east of the hamlet under an NW wind, GM 2026-07-25)
    far = _thin_belt_cluster(forest=[[1500, 200], [1520, 600], [1500, 900]])
    assert "village_windbreak_scales_with_cluster" in f(far)
    # ... and neither does a wood that is CLOSE but downwind (the lee side of the same cluster)
    lee = _thin_belt_cluster(forest=[[900, 560], [940, 600], [900, 640]])
    assert "village_windbreak_scales_with_cluster" in f(lee)


def test_labels_clear_of_other_buildings_reads_the_label_registry():
    """A caption may cover only what it NAMES, and EVERY solid feature is a victim - read from
    _LABEL_GROUP rather than a hand-written key list (GM 2026-07-26). The execution ground is the
    worked example: its three keys shipped absent from the old list, so a foreign caption over one
    passed the gate. The permission side is derived from the same registry - a group's name IS the
    caption word - so a newly classified feature needs no second entry to caption itself."""
    for key, own in (("execution_grounds", "execution ground"), ("punishment_spots", "punishment ground"), ("fire_towers", "fire tower"), ("martial_halls", "martial hall")):
        assert "labels_clear_of_other_buildings" in f(_label_map("Temple of Benten", key)), key
        assert "labels_clear_of_other_buildings" not in f(_label_map(own, key)), key
    # ...and a caption naming a DIFFERENT registered feature is still a mislabel
    assert "labels_clear_of_other_buildings" in f(_label_map("dojo", "execution_grounds"))


def test_wells_among_dwellings_counts_a_kiln_works_cottages():
    """The works' well stands among the houses it serves - they are simply recorded inside the kiln
    record rather than in M["houses"] (see s.kiln: every dwelling rule in the gate is written about
    the settlement's own housing stock, and a satellite works' cottages would be adjudicated by
    rules that were never about them). A check reading only that stock would call this well stray."""
    # a distant house so the map HAS a housing stock - the check deliberately abstains on a map
    # with no dwellings at all, which would make the negative half pass for the wrong reason
    M = _kiln_map(quarters=((500.0, 570.0),), houses=[house(100, 100)])
    M["wells"] = [well(500, 550)]
    assert "wells_among_dwellings" not in f(M)
    M["kilns"][0]["quarters"] = []
    assert "wells_among_dwellings" in f(M)


def test_a_caption_over_a_wellhead_is_caught():
    """`wells` sits in _OVERLAP_EXEMPT (a wellhead may kiss a dense-city building), and the
    classification ratchet iterates the OVERLAP registry - so a wellhead fell outside BOTH label
    registries and a caption drawn across one was invisible. Found by settlement-review round 2.
    A wellhead also has no w/h: its drawn extent is the marker radius `vr`, so classifying it was
    not enough on its own - the victim builder filtered on "w" and would have skipped it."""

    def wmap(text):
        M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1000, "H": 1000})
        M["wells"] = [well(500, 500, vr=14)]
        M["labels"] = [[440, 494, 560, 506, 1, text]]
        return M

    assert "labels_clear_of_other_buildings" in f(wmap("merchant houses & shops"))
    assert "labels_clear_of_other_buildings" not in f(wmap("well"))  # a caption may name what it covers
    assert "wells" in check_village._LABEL_GROUP


def test_theater_stage_caption_may_sit_on_its_precinct_but_not_on_the_town():
    """A stage caption is allowed onto TEMPLE ground, and nothing else it does not name.

    `theater_stage` sites the stage inside a temple/monastery precinct (and
    `theater_stage_by_temple` enforces it), so once the caption is seated by the standoff ladder
    against the stage's rotated extent, every seat within reach of its subject lands on precinct
    ground. Before this, correcting the rotation-blind caption offset simply moved Tango's caption
    off its own stage and onto a monk house, then onto a hall - a green map made worse by a fix.

    The second half is the part that matters: the allowance is scoped to `temple`, so a stage
    caption dumped on a merchant house still fires. An allowance nobody bounds is not a rule.
    """
    M = manifest(meta={"scale": "city", "ftpx": 3, "W": 2000, "H": 2000, "name": "Nowhere"})
    M["religious"] = [{"x": 500, "y": 500, "w": 300, "h": 300, "kind": "temple"}]
    M["labels"] = [[440, 480, 560, 492, 1, "theater stage"]]
    assert "labels_clear_of_other_buildings" not in check_village.gate(M, verbose=False)

    M["buildings"] = [{"x": 1200, "y": 1200, "w": 40, "h": 30, "kind": "merchant"}]
    M["labels"] = [[1180, 1190, 1240, 1202, 1, "theater stage"]]
    assert "labels_clear_of_other_buildings" in check_village.gate(M, verbose=False)


def test_labels_clear_of_other_buildings_reads_the_tilted_quad():
    # the pre-tilt box [0..3] laps the merchant, but the -30 deg glyph run swings clear below it -
    # judged by its box the caption would false-flag; judged by its true quad it is clean
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1000, "H": 1000}, buildings=[bldg(120, 106, kind="merchant", w=20, h=16)])
    M["labels"] = [[100, 100, 240, 112, 1, "stray caption", None, -30.0]]
    assert "labels_clear_of_other_buildings" not in f(M)
    M["labels"] = [[100, 100, 240, 112, 1, "stray caption"]]  # the same record level DOES lap it
    assert "labels_clear_of_other_buildings" in f(M)


def test_labels_within_image_uses_the_tilted_reach():
    lvl = [100, 20, 240, 32, 1, "near the top edge"]
    assert "labels_within_image" not in f({"meta": {}, "labels": [lvl]})
    # tilted -30, the run's high end pokes past the frame the level box sat inside
    assert "labels_within_image" in f({"meta": {}, "labels": [[*lvl[:6], None, -30.0]]})


def test_a_plural_granaries_caption_may_cover_its_own_stores():
    """'domain granaries' does not CONTAIN the group word 'granary', so the derived
    caption-permission rule alone could not permit the plural captions the wharf complexes
    carry - the synonym branch does (GM 2026-08-09, the singular/plural label question).
    Tested at CITY scale because labels_clear_of_other_buildings runs in the town/city block;
    the control proves the granaries pair is actually judged, not skipped."""
    M = {
        "meta": {"scale": "city", "W": 1000, "H": 1000},
        "granaries": [{"x": 550, "y": 560, "w": 40, "h": 24, "rot": 0, "label": "domain granaries"}],
        "labels": [[480, 550, 640, 566, 5, "domain granaries"]],
    }
    assert "labels_clear_of_other_buildings" not in f(M)
    M["labels"] = [[480, 550, 640, 566, 5, "flophouse row"]]  # a foreign caption on the stores still fires
    assert "labels_clear_of_other_buildings" in f(M)


def test_feature_022_targeted_verdict_matches_the_full_gate():
    name = "settlement_has_wells"
    full = name in set(check_village.gate(_feature_022_manifest(), verbose=False))
    targ = name in set(check_village.gate(_feature_022_manifest(), verbose=False, only={name}))
    assert full == targ


# ---- settlement_records_cluster_seeding: a rolled knob must leave a trace ---------------------
def _seedrec_M(gen="hamletgen", nucleated=True, **meta):
    M = {"meta": {"scale": "hamlet", "W": 1200, "H": 1200}}
    if gen:
        M["meta"]["generated_by"] = gen
    if nucleated:
        M["meta"]["nucleated"] = True
    M["meta"].update(meta)
    return M


def _seedrec_f(M):
    return check_village.gate(M, verbose=False, only={"settlement_records_cluster_seeding"})


def test_cluster_seeding_fires_when_neither_trace_is_recorded():
    # the Kashikawa shape (2026-08-16): rows + frontage seated every house, the cloud never ran,
    # and the rolled cluster_shape knob vanished without a trace
    assert "settlement_records_cluster_seeding" in _seedrec_f(_seedrec_M())


def test_cluster_seeding_passes_when_the_cloud_recorded_the_knob():
    assert "settlement_records_cluster_seeding" not in _seedrec_f(_seedrec_M(cluster_shape="round"))


def test_cluster_seeding_passes_when_the_seeding_mode_is_recorded():
    assert "settlement_records_cluster_seeding" not in _seedrec_f(_seedrec_M(cluster_seeding="frontage"))


def test_cluster_seeding_skips_a_dispersed_settlement():
    # no nucleated cluster = no cluster knobs to trace
    assert "settlement_records_cluster_seeding" not in _seedrec_f(_seedrec_M(nucleated=False))


def test_cluster_seeding_skips_legacy_maps():
    assert "settlement_records_cluster_seeding" not in _seedrec_f(_seedrec_M(gen=None))


def test_captions_clear_the_ways_they_stand_on_fires_and_skips_a_malformed_record() -> None:
    """0617: a caption's 3 px halo must not notch the tread its subject stands on.

    Two assertions, and the SECOND is the one with no map behind it. A label record is a flat list
    `[x0, y0, x1, y1, z, text]`, and the check guards against a shorter one - no map in the pool or
    the cohort produces one, so that `continue` is a branch the corpus cannot reach and the coverage
    gate rightly refused it. The guard is worth keeping rather than deleting: the check reads four
    positional fields off a record whose shape nothing enforces, so a truncated entry would be an
    IndexError inside the GATE, which is the worst place to discover it."""
    lane = {"pts": [(0.0, 100.0), (400.0, 100.0)], "w": 6}
    meta = {"scale": "hamlet", "ftpx": 1, "W": 1000, "H": 1000, "generated_by": "test"}

    on_the_lane = manifest(meta=meta, lanes=[lane], labels=[[180.0, 96.0, 240.0, 104.0, 20000000, "notice board"]])
    assert "captions_clear_the_ways_they_stand_on" in check_village.gate(on_the_lane, verbose=False, only={"captions_clear_the_ways_they_stand_on"})

    well_clear = manifest(meta=meta, lanes=[lane], labels=[[180.0, 300.0, 240.0, 308.0, 20000000, "notice board"]])
    assert "captions_clear_the_ways_they_stand_on" not in check_village.gate(well_clear, verbose=False, only={"captions_clear_the_ways_they_stand_on"})

    # a truncated record is SKIPPED, not crashed on, even though it sits squarely on the lane
    malformed = manifest(meta=meta, lanes=[lane], labels=[[180.0, 96.0, 240.0, 104.0]])
    assert "captions_clear_the_ways_they_stand_on" not in check_village.gate(malformed, verbose=False, only={"captions_clear_the_ways_they_stand_on"})
