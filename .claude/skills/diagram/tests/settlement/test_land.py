"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import importlib
import math
import random

import pytest

from l7r.diagram import check_village, settlement
from l7r.diagram.settlement import Settlement
from tests.settlement._builders import _crop_settlement, _hamlet_with_field, _nuc_village, _town


def test_marsh_draws_wet_scatter_and_records_it():
    s = _crop_settlement()
    s.marsh([(100, 120), (600, 100), (350, 620)])  # a triangle -> also covers the point-in-poly skip
    assert len(s.M["marshes"]) == 1 and len(s.M["marshes"][0]["poly"]) == 3
    assert s.out  # drew reeds / wet tint


def test_marsh_skips_points_on_a_paddy():
    s = _crop_settlement()
    s.field_polys.append([(300, 100), (600, 100), (600, 400), (300, 400)])  # a paddy inside the region
    s.marsh([(100, 100), (600, 100), (600, 500), (100, 500)])  # straddles the paddy - reeds over it are skipped
    assert len(s.M["marshes"]) == 1


def test_marsh_pond_fringe_skips_the_open_water():
    s = _crop_settlement()
    s.M["pond"] = [300, 300, 100, 80]  # a pond inside the region
    s.marsh([(150, 150), (450, 150), (450, 450), (150, 450)], role="pond_fringe")  # reeds rim the shore, not the open water
    assert s.M["marshes"][0]["role"] == "pond_fringe"


def test_marsh_defense_role_records_and_blocks_building():
    s = _crop_settlement()
    n0 = len(s.block_polys)
    s.marsh([(150, 150), (450, 150), (450, 450), (150, 450)], role="defense")
    assert s.M["marshes"][0]["role"] == "defense"
    assert len(s.block_polys) == n0 + 1  # the wet belt is a no-build keep-out, same as the toe


def test_marsh_rejects_an_unknown_role():
    s = _crop_settlement()
    with pytest.raises(ValueError, match="unknown marsh role"):
        s.marsh([(150, 150), (450, 150), (450, 450), (150, 450)], role="bog")


def test_commons_draws_open_scrub_and_records_it():
    s = _nuc_village()  # field to the EAST (x >= 640)
    poly = [(60, 300), (200, 320), (110, 660)]  # a TRIANGLE of open ground WEST of the field
    s.commons(poly)  # grass tufts + brush + scraggly pines
    assert len(s.M["commons"]) == 1 and len(s.M["commons"][0]["poly"]) == 3
    assert s.out  # it drew the scrub texture


def test_commons_skips_scrub_that_would_fall_on_the_paddy():
    s = _nuc_village()  # field at [(640,150),(1120,150),(1120,780),(640,780)]
    s.commons([(560, 300), (760, 300), (760, 600), (560, 600)])  # straddles the field's W edge - clumps over crops skipped
    assert len(s.M["commons"]) == 1


def test_hinterland_scrub_ring_and_marsh_downhill_each_cardinal():
    # the reed MARSH toe sits on the DOWNHILL side of the field for each cardinal slope (exercises the four
    # direction branches); the cut-over SCRUB commons fills the 3 non-toe sides (scrub is the dominant cover;
    # managed woodland is added as patches by the gen), each band centered clear of the paddy. down_deg in screen
    # angle: 90=S(+y), 270=N(-y), 0=E(+x), 180=W(-x).
    import math

    for down_deg in (90, 270, 0, 180):
        s = _hamlet_with_field(down_deg)
        s.hinterland()
        toe = [m for m in s.M["marshes"] if m["role"] == "toe"]
        grazing = [c for c in s.M["commons"] if c["role"] == "grazing"]
        # 3 outer RING bands (the non-toe sides) + 1 INTERIOR fill (over the cultivated bbox, clothing the
        # voids an irregular field leaves inside it) + 1 TOE-SIDE band. The interior fill legitimately spans
        # the paddy box; the ring bands each clear it.
        #
        # THE TOE SIDE CARRIES SCRUB TOO, since 2026-08-12. It used to be left bare because the reed toe
        # covered every inch below the crop - but the toe is now only as wide as the ground the fan waters
        # (research/water.md, "The wet toe is as wide as the FAN"), so its lateral ends are dry footslope and
        # were being covered by NOTHING: Ikegami shipped a ~267 x 193 ft corner of blank parchment with the
        # connector crossing it. The band is handed the marsh as a keep-out, which the reeds-vs-scrub
        # assertion below pins - a scrub tuft inside the reed flat would mean the two are fighting for the
        # same ground rather than meeting at its edge.
        assert len(toe) == 1 and len(grazing) == 5
        interior = [c for c in grazing if 400 <= c["x"] <= 600 and 400 <= c["y"] <= 600]
        assert len(interior) == 1  # exactly the interior fill sits over the field box
        for c in grazing:
            if c is interior[0]:
                continue
            assert not (400 <= c["x"] <= 600 and 400 <= c["y"] <= 600)  # each RING band clears the paddy box
        dx, dy = math.cos(math.radians(down_deg)), math.sin(math.radians(down_deg))
        assert (toe[0]["x"] - 500) * dx + (toe[0]["y"] - 500) * dy > 0  # toe is downhill of field center


def test_hinterland_honors_hamlet_keepout_and_dry_plot_extent():
    # a hamlet keep-out (from M['houses']) and the dry-hatake extent are both folded in: the house sits where a
    # ring + the marsh toe overlap it, so the avoid-skip fires in BOTH commons and marsh; dry_plots widen the
    # cultivated bbox the woodland sets back from.
    s = _hamlet_with_field(90)
    s.M["houses"] = [{"x": 300, "y": 500, "w": 20, "h": 14, "rot": 0}]
    s.M["dry_plots"] = [{"poly": [[610, 400], [720, 400], [720, 520], [610, 520]], "crop": "soy", "theta": 0.0}]
    s.hinterland()
    assert s.M["commons"] and s.M["marshes"]


def test_hinterland_flags_default_downdeg_and_empty_field():
    s = _hamlet_with_field(90)
    s.hinterland(commons=False)  # marsh only
    assert not s.M["commons"] and len(s.M["marshes"]) == 1
    s2 = _hamlet_with_field(90)
    s2.hinterland(marsh=False)  # commons only
    assert s2.M["commons"] and not s2.M["marshes"]
    s3 = _hamlet_with_field(90)
    s3.hinterland(down_deg=None)  # None -> reads meta down_deg (90 = south)
    assert s3.M["marshes"][0]["y"] > 500
    empty = Settlement(1000, 1000, seed=1)
    empty.meta(name="E", scale="hamlet")
    empty.hinterland()  # no field_polys -> early return
    assert not empty.M["commons"] and not empty.M["marshes"]


def test_commons_glyph_variants_draw_and_record_each_role():
    # the three distinct land-cover looks exercised directly (independent of the village gens): woodland =
    # tree CROWNS, pasture = open GRASS (no pines), commons/grazing = grass + a few scraggly PINES. Each is
    # given a non-empty `avoid` keep-out so the avoid-skip is exercised too. A marsh keep-out is checked as well.
    poly = [(200, 200), (800, 200), (800, 800), (200, 800)]
    keepout = [[(400, 400), (600, 400), (600, 600), (400, 600)]]  # a central keep-out the scatter stays out of
    for role in ("woodland", "pasture", "commons", "grazing"):
        s = Settlement(1000, 1000, seed=3)
        s.meta(name="C", scale="hamlet")
        s.commons(poly, role=role, avoid=keepout)
        assert s.M["commons"][-1]["role"] == role and s.out  # recorded + something drawn
    sm = Settlement(1000, 1000, seed=3)
    sm.meta(name="C", scale="hamlet")
    sm.marsh(poly, avoid=keepout)
    assert sm.M["marshes"][-1]["role"] == "toe"


def test_hinterland_skip_sides_drops_a_scrub_band():
    # skip_sides suppresses the scrub band on a named frame side (e.g. a forest flank): down_deg=90 -> toe=bottom,
    # non-toe = top/left/right (3 ring bands); skipping "right" leaves 2 ring bands, PLUS the interior fill = 3.
    s = _hamlet_with_field(90)
    s.hinterland(skip_sides=("right",))
    # 2 ring bands + the interior fill + the toe-side band (see the cardinal test for why the toe side is
    # now clothed) = 4.
    assert [c["role"] for c in s.M["commons"]].count("grazing") == 4
    # ...and skipping the TOE side drops its band too, rather than laying scrub where a gen wants none
    s2 = _hamlet_with_field(90)
    s2.hinterland(skip_sides=("bottom",))
    assert [c["role"] for c in s2.M["commons"]].count("grazing") == 4  # 3 ring (top/left/right) + interior, no toe band


def test_hinterland_dispersed_keepout_is_per_homestead():
    # DISPERSED settlements keep out each HOMESTEAD individually, not the (map-spanning) bbox of the ringing
    # farms - otherwise no ground cover could be laid inside the ring at all (the Akagahara bare-void bug). With
    # meta.nucleated False and two far-apart farmsteads, the open ground BETWEEN them still carries scrub.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="D", scale="hamlet", down_deg=90, nucleated=False)
    s.field_polys.append([(400, 400), (600, 400), (600, 600), (400, 600)])
    s.M["houses"] = [{"x": 250, "y": 250, "w": 46, "h": 28}, {"x": 750, "y": 250, "w": 46, "h": 28}]
    s.hinterland()
    # the interior fill lands over the field box (proving cover was NOT blanket-forbidden by a map-wide keep-out)
    grazing = [c for c in s.M["commons"] if c["role"] == "grazing"]
    assert any(400 <= c["x"] <= 600 and 400 <= c["y"] <= 600 for c in grazing)


def test_perimeter_dike_draws_an_irregular_earthwork_band():
    s = Settlement(1400, 1400, seed=3)
    s.meta(name="D", scale="hamlet", ftpx=1, toscale=True, households=8, field_archetype="polder_grid")
    env = [(200, 200), (200, 1000), (900, 1000), (900, 200), (200, 200)]
    s.perimeter_dike(env, seed=5)
    dk = s.M["dikes"][0]
    assert dk["label"] == "perimeter dike"
    assert dk["w_max"] >= 1.4 * dk["w_min"]  # varying width, not a uniform stroke
    assert len(dk["outline"]) >= 60  # a smoothed organic band, not a 4-corner rectangle
    # the band stays a ring around the grid (outer points sit outside the inner env, none wildly off-map)
    assert all(0 <= x <= 1400 and 0 <= y <= 1400 for x, y in dk["outline"])
    # a label was recorded, and drawing is deterministic per seed
    assert any(lbl[5] == "perimeter dike" for lbl in s.M["labels"] if len(lbl) > 5)
    s2 = Settlement(1400, 1400, seed=3)
    s2.meta(name="D", scale="hamlet", ftpx=1, toscale=True, households=8, field_archetype="polder_grid")
    s2.perimeter_dike(env, seed=5)
    assert s2.M["dikes"][0]["outline"] == dk["outline"]
    # an empty label skips the caption but still draws + records the band
    s3 = Settlement(1400, 1400, seed=3)
    s3.meta(name="D", scale="hamlet", ftpx=1, toscale=True, households=8, field_archetype="polder_grid")
    s3.perimeter_dike(env, seed=5, label="")
    assert s3.M["dikes"] and not any(len(lbl) > 5 and lbl[5] == "perimeter dike" for lbl in s3.M.get("labels", []))


def test_village_grove_skips_the_dike_bank():
    # a windbreak belt laid ACROSS the perimeter dike must place NO clump on the earthwork bank
    # (GM 2026-07-22: the dike carries only its own soil-binding trees).
    s = Settlement(1400, 1400, seed=3)
    s.meta(name="G", scale="hamlet", ftpx=1, toscale=True, households=8, field_archetype="polder_grid")
    s.perimeter_dike([(200, 200), (200, 1000), (900, 1000), (900, 200), (200, 200)], seed=5)
    dike = s.M["dikes"][0]["outline"]

    def pip(x, y, poly):
        c, j = False, len(poly) - 1
        for i in range(len(poly)):
            xi, yi, xj, yj = poly[i][0], poly[i][1], poly[j][0], poly[j][1]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
                c = not c
            j = i
        return c

    s.village_grove([(150, 150), (360, 150), (360, 280), (150, 280)], role="windbreak")  # a belt straddling the NW dike
    clumps = s.M["village_groves"][-1]["clumps"]
    assert clumps and not any(pip(cx, cy, dike) for cx, cy in clumps)  # some clumps, none on the dike


def test_clearings_keep_scrub_off_sacred_and_funerary_ground():
    """Feature: a swept verge around shrine/torii/graves. `_clear_ground` grows the footprint by `extra`
    (bscale-scaled) into `self.clearings`, which the hinterland scatter skips - but building placement
    (block_polys) and groves are untouched, so a shrine's preserved grove is unaffected."""
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="C", scale="village", ftpx=1, down_deg=90)
    n_block = len(s.block_polys)
    s._clear_ground(600, 600, 40, 30, 58)
    assert len(s.clearings) == 1 and len(s.block_polys) == n_block  # clearings, NOT block_polys
    poly = s.clearings[0]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    # the verge is an ORGANIC blob (irregular inward bays), not the padded rectangle: 16 edge samples,
    # more than 4 distinct x values, contained in the padded rect (bays-only - the claim never grows),
    # and still generously containing the footprint (a bay cuts at most ~55% of the 58px collar)
    assert len(poly) == 16 and len({round(px, 1) for px in xs}) > 4
    assert min(xs) >= 600 - 20 - 58 and max(xs) <= 600 + 20 + 58 and min(ys) >= 600 - 15 - 58 and max(ys) <= 600 + 15 + 58
    assert all(settlement.point_in_poly(fx, fy, poly) for fx, fy in [(580, 585), (620, 585), (620, 615), (580, 615)])
    # shrine_hall with a torii registers a clearing for BOTH the hall and the arch
    s2 = Settlement(1200, 1200, seed=1)
    s2.meta(name="C2", scale="village", ftpx=1, down_deg=90)
    s2.shrine_hall(600, 600, "Shrine", torii=[(600, 680)], torii_count=1)  # pinned so the clearing count is stable under the per-temple roll
    assert len(s2.clearings) == 2  # the hall + the one torii
    # a cemetery registers one too
    s3 = Settlement(1200, 1200, seed=1)
    s3.meta(name="C3", scale="village", ftpx=1, down_deg=90)
    s3.cemetery(600, 600, 90, 60, label="burial ground")
    assert len(s3.clearings) == 1


def test_clear_ground_is_deterministic_and_preserves_the_rng_stream():
    """The organic verge is seeded from its own footprint: identical args -> identical blob (render-sync
    determinism), and the map's global RNG stream is untouched (saved/restored), so adding or reshaping
    a collar can never shift any other feature's random draws."""
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="D", scale="village", ftpx=1, down_deg=90)
    random.seed(99)
    expect = random.random()
    random.seed(99)
    s._clear_ground(600, 600, 40, 30, 58)
    assert random.random() == expect  # the stream is exactly where it was
    s2 = Settlement(1200, 1200, seed=7)  # different map seed, same collar args
    s2.meta(name="D2", scale="village", ftpx=1, down_deg=90)
    s2._clear_ground(600, 600, 40, 30, 58)
    assert s.M["clearings"][0]["poly"] == s2.M["clearings"][0]["poly"]


def test_clear_ground_dedupes_same_center_registrations():
    """The reserve_clearing-then-feature pattern registers the same collar twice (the feature's own call
    lands within a few px of the reserve, sometimes with a different footprint/extra). The duplicate
    REUSES the first blob verbatim - guard and late collar can never disagree about the swept outline -
    while a genuinely different center gets its own blob."""
    s = Settlement(1200, 1200, seed=1)
    s.meta(name="E", scale="village", ftpx=1, down_deg=90)
    s._clear_ground(600, 600, 60, 46, 30)  # the gen's reserve
    s._clear_ground(600, 602, 40, 30, 58)  # the feature's own late registration: 2px off, different size
    assert len(s.clearings) == 2 and s.clearings[0] == s.clearings[1]
    assert s.M["clearings"][0]["poly"] == s.M["clearings"][1]["poly"]
    s._clear_ground(900, 900, 40, 30, 58)  # a different feature elsewhere: its own blob
    assert len(s.clearings) == 3 and s.clearings[2] != s.clearings[1]


def test_perimeter_dike_gap_off_band_still_draws_full_loop():
    # GM 2026-07-22 (issue 1): perimeter_dike NOTCHES the earthwork at each sluice-crossing gap. A gap point
    # placed FAR from the band keeps every dense point, so the band draws as one full loop (the defensive
    # all-kept branch) and the gap is still recorded on the manifest.
    s = Settlement(1000, 1000, seed=1)
    env = [(200, 200), (800, 200), (800, 800), (200, 800)]
    s.perimeter_dike(env, seed=7, gaps=[(5000, 5000)])
    assert s.M["dikes"] and s.M["dikes"][0]["gaps"] == [[5000.0, 5000.0]]


def test_perimeter_dike_notches_the_band_at_a_gap_on_it():
    # a gap ON the band splits the earthwork into runs between the notches (it records the gap and still
    # draws a dike); the through-gap is where a sluice channel crosses.
    s = Settlement(1000, 1000, seed=2)
    env = [(200, 200), (800, 200), (800, 800), (200, 800)]
    s.perimeter_dike(env, seed=3, gaps=[(500, 200), (500, 800)])
    assert s.M["dikes"] and len(s.M["dikes"][0]["gaps"]) == 2


# ---- near_ring_cropland (feature 013): channel-free dry/garden tiler that packs the flat near ring.
def test_near_ring_cropland_rejects_an_unknown_density():
    s = _town()
    with pytest.raises(ValueError, match="near_ring_density"):
        s.near_ring_cropland((0, 0, 1000, 1000), density="lush")


def test_near_ring_cropland_returns_zero_for_a_degenerate_bbox():
    s = _town()
    assert s.near_ring_cropland((100, 100, 105, 900), density="dense") == 0


def test_near_ring_cropland_fills_clear_ground_and_records_dry_plots():
    s = _town()
    n = s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=3)
    assert n > 0
    assert len(s.M["dry_plots"]) == n
    assert len(s.dry_polys) == n  # recorded as no-build cropland
    # every plot carries the dry-plot shape the checks read
    assert all(set(p) >= {"poly", "crop", "theta"} for p in s.M["dry_plots"])


def test_near_ring_cropland_density_tiers_are_monotonic():
    def count(tier):
        s = _town()
        return s.near_ring_cropland((0, 0, 1000, 1000), density=tier, seed=7)

    assert count("dense") > count("medium") > count("thin") > 0


def test_near_ring_cropland_reads_meta_near_ring_density_when_density_is_none():
    s = _town()
    s.meta(near_ring_density="thin")
    thin = s.near_ring_cropland((0, 0, 1000, 1000), density=None, seed=2)
    s2 = _town()
    dense = s2.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=2)
    assert thin < dense  # the meta default ('thin') fills less than an explicit 'dense'


def test_near_ring_cropland_can_be_all_garden_or_all_grain():
    s = _town()
    s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=1, garden_frac=1.0)
    assert s.M["dry_plots"] and all(p["crop"] == "garden" for p in s.M["dry_plots"])
    s2 = _town()
    s2.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=1, garden_frac=0.0)
    assert s2.M["dry_plots"] and all(p["crop"] != "garden" for p in s2.M["dry_plots"])


def test_near_ring_cropland_skips_fields_structures_hill_and_groves():
    s = _town()
    s.M["hill"] = [500, 200, 180, 120]  # a hill in the north
    s.field_polys.append([(0, 700), (400, 700), (400, 1000), (0, 1000)])  # a paddy block, SW
    s.M["houses"] = [{"x": 800, "y": 800, "w": 40, "h": 30, "rot": 0}]  # a dwelling, SE
    s.M["village_groves"] = [{"poly": [[600, 600], [760, 600], [760, 760], [600, 760]], "role": "copse", "clumps": [[680, 680]]}]
    s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=5)
    from l7r.diagram.settlement import point_in_poly

    for p in s.M["dry_plots"]:
        cx = sum(v[0] for v in p["poly"]) / 4
        cy = sum(v[1] for v in p["poly"]) / 4
        assert not (((cx - 500) / (180 * 1.35)) ** 2 + ((cy - 200) / (120 * 1.35)) ** 2 <= 1.0)  # off the hill
        assert not point_in_poly(cx, cy, [(0, 700), (400, 700), (400, 1000), (0, 1000)])  # off the paddy
        assert not (760 >= cx >= 600 and 760 >= cy >= 600)  # off the grove belt
        assert not (780 >= cx >= 620 and 780 >= cy >= 620)  # not covering the grove clump


def test_near_ring_cropland_skips_a_grove_clump_outside_its_belt_poly():
    # a clump can sit just past its loose belt poly; the per-plot clump-bbox guard (not the belt-poly
    # test) is what keeps a plot off it, so no dry plot may cover the stray clump
    s = _town()
    s.M["village_groves"] = [{"poly": [], "clumps": [[500, 500]]}]  # empty belt poly -> only the clump guard applies
    s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=6)
    for p in s.M["dry_plots"]:
        qx0, qy0 = min(v[0] for v in p["poly"]), min(v[1] for v in p["poly"])
        qx1, qy1 = max(v[0] for v in p["poly"]), max(v[1] for v in p["poly"])
        assert not (qx0 - 12 <= 500 <= qx1 + 12 and qy0 - 12 <= 500 <= qy1 + 12)


def test_near_ring_cropland_keeps_a_city_ring_outside_the_wall():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="C", scale="city")
    s.M["wall"] = [[300, 300], [700, 300], [700, 700], [300, 700]]  # a square rampart
    s.near_ring_cropland((0, 0, 1000, 1000), density="dense", seed=4)
    from l7r.diagram.settlement import point_in_poly

    for p in s.M["dry_plots"]:
        cx = sum(v[0] for v in p["poly"]) / 4
        cy = sum(v[1] for v in p["poly"]) / 4
        assert not point_in_poly(cx, cy, [(300, 300), (700, 300), (700, 700), (300, 700)])  # no cropland inside the wall


# ---- near_ring_paddy (feature 014): moat/stream/edge-watered paddy basins, the dominant near-ring crop.
def test_near_ring_paddy_returns_zero_for_a_degenerate_bbox():
    s = _town()
    assert s.near_ring_paddy((100, 100, 105, 900)) == 0


def test_near_ring_paddy_places_off_edge_basins_recorded_as_paddy_fields():
    s = _town()
    n = s.near_ring_paddy((0, 0, 1000, 1000), seed=2, cell_ft=180)
    assert n > 0
    made = [fld for fld in s.M["fields"] if fld["name"].startswith("nrp_")]
    assert len(made) == n and all(fld["kind"] == "paddy" for fld in made)


def test_near_ring_paddy_skips_interior_ground_with_no_reachable_water():
    # a town (no moat) with a big frame: interior basins far from the edge have no water -> skipped;
    # only the off-edge band is filled. So no placed basin sits deep in the middle.
    s = Settlement(1600, 1600, seed=3)
    s.meta(name="T", scale="town")
    s.near_ring_paddy((0, 0, 1600, 1600), seed=3, cell_ft=150)
    for fld in s.M["fields"]:
        if fld["name"].startswith("nrp_"):
            b = fld["bbox"]
            touches_edge = b[0] < 60 or b[1] < 60 or b[2] > 1540 or b[3] > 1540
            assert touches_edge  # only edge-watered basins were placed


def test_near_ring_paddy_waters_a_basin_from_a_pond_ring():
    # an INTERIOR bbox (never touches the frame edge, no moat) - so a basin can ONLY be watered by the pond ring
    s = Settlement(1400, 1400, seed=5)
    s.meta(name="T", scale="town")
    s.M["pond"] = [700, 700, 190, 190]
    n = s.near_ring_paddy((450, 450, 950, 950), seed=5, cell_ft=120)
    assert n > 0 and any(fld["name"].startswith("nrp_") for fld in s.M["fields"])


def test_near_ring_paddy_keeps_basins_off_streams_and_the_hill():
    s = Settlement(1400, 1400, seed=4)
    s.meta(name="T", scale="town")
    s.M["hill"] = [700, 200, 200, 140]
    s.M["streams"] = [{"poly": [[700, 0], [700, 1400]], "w": 8}]  # a stream down the middle
    s.near_ring_paddy((0, 0, 1400, 1400), seed=4, cell_ft=150)
    from l7r.diagram.settlement import seg_dist

    for fld in s.M["fields"]:
        if fld["name"].startswith("nrp_"):
            for vx, vy in fld["outline"]:
                assert min(seg_dist(vx, vy, (700, 0), (700, 1400)), 999) > 14  # off the stream
                assert not (((vx - 700) / (200 * 1.35)) ** 2 + ((vy - 200) / (140 * 1.35)) ** 2 <= 1.0)  # off the hill


def test_near_ring_paddy_moat_feeds_a_walled_city_basin_with_a_channel():
    s = Settlement(1400, 1400, seed=6)
    s.meta(name="C", scale="city")
    s.M["wall"] = [[500, 500], [900, 500], [900, 900], [500, 900]]
    s.M["moat"] = [[480, 480], [920, 480], [920, 920], [480, 920]]
    s.M["moat_width"] = 22
    # a big building band just outside the west moat: a basin west of it can only be moat-fed by a
    # channel that would CROSS the building, so that basin is skipped (the channel-clearance keep-out)
    s.M["buildings"] = [{"x": 430, "y": 700, "w": 60, "h": 340, "rot": 0, "kind": "warehouse"}]
    # a road + a rect-record cemetery: both keep-out builders must run (these paths were exercised by
    # the pool maps until the 2026-07-23 combs-only doctrine retired the basins from every gen)
    s.M["road"] = [[0, 1300], [1400, 1300]]
    s.M["cemeteries"] = [{"x": 1200, "y": 200, "w": 60, "h": 40}]
    n = s.near_ring_paddy((0, 0, 1400, 1400), seed=6, cell_ft=200)
    assert n > 0
    # interior (non-off-edge) basins are moat-fed: there is at least one moat->field channel
    assert any((c.get("frm") or {}).get("kind") == "moat" for c in s.M.get("channels", []))
    # no moat channel crosses the building (the clearance keep-out held)
    from l7r.diagram.settlement import seg_dist

    for c in s.M.get("channels", []):
        if (c.get("frm") or {}).get("kind") == "moat":
            assert seg_dist(430, 700, c["poly"][0], c["poly"][-1]) > 25


def test_near_ring_paddy_respects_the_moat_current_when_the_moat_is_fed():
    # a moat fed by a stream from the north flows south; every moat intake must tap upstream of its basin
    s = Settlement(1600, 1600, seed=7)
    s.meta(name="C", scale="city")
    s.M["wall"] = [[600, 600], [1000, 600], [1000, 1000], [600, 1000]]
    s.M["moat"] = [[580, 580], [1020, 580], [1020, 1020], [580, 1020]]
    s.M["moat_width"] = 22
    s.M["streams"] = [{"poly": [[800, 580], [800, 200]], "w": 8}]  # feeder entering the moat top, coming from the north
    s.near_ring_paddy((0, 0, 1600, 1600), seed=7, cell_ft=220)
    for c in s.M.get("channels", []):
        if (c.get("frm") or {}).get("kind") == "moat":
            (_sx, sy), (_ex, ey) = c["poly"][0], c["poly"][-1]
            assert ey - sy >= -8  # field-end not upstream (north) of the moat tap - flows with the southward current


def test_near_ring_paddy_keeps_basins_off_a_polygon_cemetery():
    # a funerary ground recorded as a POLYGON (not an x/w dict) still sets the paddy back (funerary_set_back_from_water)
    s = Settlement(1400, 1400, seed=9)
    s.meta(name="C", scale="city")
    s.M["wall"] = [[560, 560], [840, 560], [840, 840], [560, 840]]
    s.M["moat"] = [[540, 540], [860, 540], [860, 860], [540, 860]]
    s.M["moat_width"] = 22
    s.M["cemeteries"] = [{"poly": [[900, 900], [1050, 900], [1050, 1050], [900, 1050]], "label": "graveyard"}]
    s.near_ring_paddy((0, 0, 1400, 1400), seed=9, cell_ft=200)
    for fld in s.M["fields"]:
        if fld["name"].startswith("nrp_"):
            for vx, vy in fld["outline"]:
                assert not (900 - 60 <= vx <= 1050 + 60 and 900 - 60 <= vy <= 1050 + 60)  # set back from the grave poly


def test_dike_top_houses_seats_a_single_file_on_the_crest():
    # GM 2026-07-24 (settlements.md 'Polder siting Q&A'): the ISLET-polder settlement form - houses in
    # single file ON the dike crest, each on a widened-crest platform, tagged on_dike in the manifest.

    s = Settlement(1400, 1400, seed=5)
    s.meta(name="DT", scale="hamlet", ftpx=1, toscale=True, households=8, terrain="low", field_archetype="polder_grid")
    env = [(300, 300), (1100, 300), (1100, 1100), (300, 1100)]
    s.perimeter_dike(env, seed=7, gaps=[(500, 300), (700, 300)])
    dk = s.M["dikes"][0]
    # the crest centerline is recorded, and every crest point sits on the band
    assert len(dk["crest"]) >= 60
    assert all(check_village.poly_dist(cx, cy, dk["outline"]) <= 6 for cx, cy in dk["crest"])
    st = random.getstate()
    n = s.dike_top_houses(8, seed=11, span=(0.0, 0.25), gap_clear=60.0)  # the top (north) run, which carries both sluice gaps
    assert random.getstate() == st  # stream-neutral: the helper never ripples the map's main rng
    tagged = [h for h in s.M["houses"] if h.get("on_dike")]
    assert n == len(tagged) and 4 <= n < 8  # the sluice-gap skips cost sites - nobody builds over the notch
    for h in tagged:
        assert check_village.poly_dist(h["x"], h["y"], dk["outline"]) <= 14  # seated on the band
        assert all(math.hypot(h["x"] - gx, h["y"] - gy) >= 60 for gx, gy in ((500, 300), (700, 300)))
        assert h["platform"][0] > h["w"] and h["platform"][1] > h["h"]  # the widened-crest pad outsizes the house
    assert s.M["meta"]["settlement_form"] == "dike_top"  # the helper declares the form
    # single file: a crowded call self-spaces (spacing skips), so a short span caps well under the ask
    n2 = s.dike_top_houses(30, seed=3, span=(0.5, 0.75))
    assert 0 < n2 < 30
    # determinism: an identical settlement re-run lands identical houses
    s2 = Settlement(1400, 1400, seed=5)
    s2.meta(name="DT", scale="hamlet", ftpx=1, toscale=True, households=8, terrain="low", field_archetype="polder_grid")
    s2.perimeter_dike(env, seed=7, gaps=[(500, 300), (700, 300)])
    s2.dike_top_houses(8, seed=11, span=(0.0, 0.25), gap_clear=60.0)
    assert [h for h in s2.M["houses"] if h.get("on_dike")] == tagged


def test_farmsteads_keep_dike_top_houses():
    # farmsteads() rebuilds M['houses'] from the pending-bundle survivors; dike-top houses are not
    # pending farmsteads, so they must survive the rebuild rather than being silently dropped.
    s = Settlement(1400, 1400, seed=5)
    s.meta(name="DT", scale="hamlet", ftpx=1, toscale=True, households=8, terrain="low", field_archetype="polder_grid")
    s.perimeter_dike([(300, 300), (1100, 300), (1100, 1100), (300, 1100)], seed=7)
    s.dike_top_houses(4, seed=11, span=(0.0, 0.25))
    before = [h for h in s.M["houses"] if h.get("on_dike")]
    assert before
    s.farmsteads()
    assert [h for h in s.M["houses"] if h.get("on_dike")] == before


def test_marsh_waterside_role():
    # the un-reclaimed wet wild outside a polder dike (settlements.md 'Polder siting Q&A'): a valid
    # role, recorded like any marsh; an unknown role still raises.
    s = Settlement(1400, 1400, seed=5)
    s.meta(name="WS", scale="hamlet", ftpx=1, toscale=True)
    s.marsh([(0, 200), (260, 200), (260, 1200), (0, 1200)], role="waterside")
    assert s.M["marshes"][-1]["role"] == "waterside"
    with pytest.raises(ValueError):
        s.marsh([(0, 0), (10, 0), (10, 10)], role="lagoon")


def test_commons_bare_records_the_claim_and_draws_nothing():
    """render='bare' claims the ground (full record: role, poly, render) but scatters no scrub -
    the GM's no-glyphs-on-claimed-capital-ground ruling (021)."""
    s = Settlement(800, 800, seed=9)
    svg_before = len(s.out)
    s.commons([(100, 100), (300, 100), (300, 260), (100, 260)], role="drill ground", render="bare")
    rec = s.M["commons"][-1]
    assert rec["role"] == "drill ground" and rec["poly"][0] == [100, 100]
    assert len(s.out) == svg_before  # no ink


def test_a_lane_is_walked_back_off_the_reeds_and_dropped_if_the_whole_leg_is_wet():
    """THE RULE (GM 2026-08-12): "paths don't pass through marshland". A way laid AFTER its water
    stops on the dry side of the reeds - and a leg that is wet along its whole length is dropped
    rather than shortened to a stub, except where dropping it would leave no way at all.

    Both directions matter: a two-point skeleton arm has no vertex to drop, which is exactly the
    case the first version of this silently did nothing for."""
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="Reeds", scale="hamlet", ftpx=1, toscale=True, households=12)
    s.M["marshes"].append({"x": 900, "y": 600, "w": 400, "h": 400, "rot": 0, "role": "toe", "seq": 1, "poly": [[700.0, 400.0], [1100.0, 400.0], [1100.0, 800.0], [700.0, 800.0]]})
    trimmed = s.trim_off_marsh([(200.0, 600.0), (1000.0, 600.0)])
    assert trimmed[0] == (200.0, 600.0), "the dry end is left where it is"
    assert trimmed[-1][0] < 700.0, f"the wet end must be walked back out of the reeds, got {trimmed[-1]}"
    # a THREE-point way whose last leg lies wholly in the marsh loses that leg outright
    dropped = s.trim_off_marsh([(200.0, 600.0), (500.0, 600.0), (900.0, 600.0), (920.0, 600.0)])
    assert all(q[0] < 700.0 for q in dropped), f"every surviving point must be dry, got {dropped}"
    # ...and a way with nowhere dry to retreat to still returns something drawable
    assert len(s.trim_off_marsh([(800.0, 600.0), (900.0, 600.0)])) >= 2
    assert s.trim_off_marsh([(200.0, 600.0)]) == [(200.0, 600.0)], "a stub shorter than a segment is returned untouched"


def test_a_map_with_no_field_has_no_wet_toe_to_ask_about():
    """`toe_band` is asked for BEFORE the marsh is drawn, by a router that may run on a map with no
    paddy at all. It answers with no band rather than raising, so the caller needs no special case."""
    s = Settlement(800, 800, seed=1)
    s.meta(name="Dry", scale="hamlet", ftpx=1, toscale=True, households=12)
    assert s.toe_band() == []


# ---- feature 120: the composed LandMixin surface -------------------------------------------------
# The one thing a package split can break SILENTLY. A member dropped by the transformer yields a
# package that imports cleanly, type-checks cleanly under mypy --strict, and draws nothing - it
# surfaces only when whichever generator calls that member happens to run. A member defined TWICE
# yields a working import, a clean typecheck, and one silently dead implementation, because the MRO
# just picks the first base. Contract: specs/120-land-package/contracts/surface.md.
#
# This split has a wrinkle its seven predecessors did not: three members left the package entirely
# for homestead_parts.py, so the surface that must survive is the one on the composed SETTLEMENT,
# not the one on LandMixin. Pinning it to LandMixin would fail for a relocation that is correct, and
# training a reader to move names out of the pin is exactly the reflex that lets a real loss through.

_LAND_SURFACE = frozenset(
    {
        # public - called from pool gens, wip/, hamletgen and other engine modules
        "commons",
        "dike_top_houses",
        "hinterland",
        "marsh",
        "near_ring_cropland",
        "near_ring_paddy",
        "perimeter_dike",
        "reserve_clearing",
        "toe_band",
        "trim_off_marsh",
        # private - reached through self., including from OUTSIDE the package
        "_attach_grove",
        "_clear_ground",
        "_farmstead_nudges",
        "_find_appurtenances",
    }
)

# The three that deliberately left the package. Recorded as its own pin because the RELOCATION is a
# decision, not an accident: every function they call was already in homestead_parts.py, and a
# future session moving them back into land/ should have to say so rather than drift.
_RELOCATED_TO_HOMESTEAD_PARTS = frozenset({"_attach_grove", "_farmstead_nudges", "_find_appurtenances"})


def _own(cls: type) -> set[str]:
    """Every non-dunder name this class body defines - data attributes included, not just callables."""
    return {k for k in vars(cls) if not k.startswith("__")}


def _land_sub_mixins() -> list[type]:
    from l7r.diagram.settlement.land import LandMixin

    return [c for c in LandMixin.__mro__ if c is not LandMixin and c is not object]


def test_no_member_of_the_pre_split_land_surface_is_lost():
    # SUPERSET, not equality, deliberately: a later decomposition legitimately adds named private
    # helpers, and equality would turn every such change into a contract edit.
    composed = set().union(*(_own(c) for c in Settlement.__mro__))
    assert composed >= _LAND_SURFACE, f"missing={sorted(_LAND_SURFACE - composed)}"


def test_no_land_member_is_defined_in_two_sub_mixins():
    # The census above cannot see this: a name defined in two bases still appears in the union, so a
    # duplicate passes it, passes the import, passes mypy --strict, and runs whichever definition the
    # MRO reaches first - leaving the other as dead code a future reader will edit believing it live.
    # The transformer refuses such a partition, but the transformer is a one-shot script; this test
    # outlives it and covers the member somebody adds by hand later.
    seen: dict[str, str] = {}
    dupes: list[str] = []
    for cls in _land_sub_mixins():
        for name in _own(cls):
            if name in seen:
                dupes.append(f"{name} in both {seen[name]} and {cls.__name__}")
            seen[name] = cls.__name__
    assert not dupes, f"defined twice: {sorted(dupes)}"


def test_the_relocated_farmstead_helpers_live_in_homestead_parts_not_in_land():
    from l7r.diagram.settlement.homestead_parts import HomesteadPartsMixin
    from l7r.diagram.settlement.land import LandMixin

    land_names = set().union(*(_own(c) for c in LandMixin.__mro__))
    assert _own(HomesteadPartsMixin) >= _RELOCATED_TO_HOMESTEAD_PARTS, f"not relocated: {sorted(_RELOCATED_TO_HOMESTEAD_PARTS - _own(HomesteadPartsMixin))}"
    assert not (_RELOCATED_TO_HOMESTEAD_PARTS & land_names), f"still in land/: {sorted(_RELOCATED_TO_HOMESTEAD_PARTS & land_names)}"


def test_surface_water_dist_survives_the_split_at_both_import_paths():
    # It is the one MODULE-LEVEL member, defined after the class, so a transformer that sliced only
    # the class body would have dropped it and broken three consumers at import time.
    #
    # import_module rather than a plain `import l7r.diagram.settlement.land`: ruff reads the latter
    # as unused and deletes it, which leaves the assertion below resolving `settlement.land` only
    # through the parent package's own re-export side effect. That still passes, so the weakening is
    # silent - exactly the failure mode this whole contract exists to prevent.
    land = importlib.import_module("l7r.diagram.settlement.land")

    assert settlement.surface_water_dist is land.surface_water_dist
    assert settlement.surface_water_dist({"channels": [], "streams": []}, 0, 0) == 1e9
