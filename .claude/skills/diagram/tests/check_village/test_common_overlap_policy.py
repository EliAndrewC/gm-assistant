"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

from l7r.diagram import check_village
from tests.check_village._builders import _gate_parts, bldg, house, manifest


def test_poly_gap_overlap_containment_edgecross_and_separated():
    # poly_gap: 0 when one contains the other, 0 when edges CROSS with no vertex inside, else the min distance.
    sq = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert check_village.poly_gap(sq, [[3, 3], [5, 3], [5, 5], [3, 5]]) == 0.0  # containment
    bar1 = [[0, 4], [10, 4], [10, 6], [0, 6]]  # a + cross: edges cross,
    bar2 = [[4, 0], [6, 0], [6, 10], [4, 10]]  # no vertex inside the other
    assert check_village.poly_gap(bar1, bar2) == 0.0
    assert check_village.poly_gap(sq, [[20, 0], [30, 0], [30, 10], [20, 10]]) == 10.0  # separated by 10


def test_matrix_extracts_a_ward_gates_parts_and_splits_off_the_guard_box():
    got = [k for k, *_ in check_village.matrix_extents({"meta": {"scale": "city"}, "kido": [_gate_parts()]})]
    assert sorted(got) == ["kido", "kido_guard_box"]
    # a gate that records no `guard` degrades to all-gateway rather than crashing, and a degenerate
    # part (fewer than 3 corners) is skipped
    bare = {"x": 400, "y": 500, "rot": 0, "parts": [[[380, 490], [420, 490], [420, 510], [380, 510]], [[1, 1], [2, 2]]]}
    assert [k for k, *_ in check_village.matrix_extents({"meta": {"scale": "city"}, "kido": [bare]})] == ["kido"]


def test_the_parts_of_one_gate_do_not_accuse_each_other():
    # every part shares one object id, so the annex-on-its-own-parent test spares the glyph's pieces
    assert not [v for v in check_village.matrix_violations({"meta": {"scale": "city"}, "kido": [_gate_parts()]}) if "kido" in (v[0], v[1])]


def test_matrix_sees_the_multi_road_list_and_a_flower_beds_outline():
    # `roads` (the multi-road list) and `flower_fields` (which stores its ring as `outline`, not
    # `poly`) were the other two classified-but-never-extracted keys found by the same audit
    on_road = {"meta": {"scale": "city"}, "roads": [{"pts": [[300, 500], [700, 500]], "w": 26}], "buildings": [bldg(500, 500, kind="merchant_house")]}
    assert ("roads", "buildings") in {(a, b) for a, b, _, _ in check_village.matrix_violations(on_road)} or ("buildings", "roads") in {
        (a, b) for a, b, _, _ in check_village.matrix_violations(on_road)
    }
    bed = {"meta": {"scale": "city"}, "flower_fields": [{"kind": "chrysanthemum", "outline": [[400, 400], [600, 400], [600, 600], [400, 600]]}], "buildings": [bldg(500, 500, kind="merchant_house")]}
    assert [v for v in check_village.matrix_violations(bed) if "flower_fields" in (v[0], v[1])]


def test_clip_and_onmap_edge_handle_a_fully_offmap_field():
    # a field lying entirely outside the map rect clips to nothing and contributes no on-map edge
    poly = [[-500, -500], [-300, -500], [-300, -300], [-500, -300]]
    assert check_village.clip_poly_rect(poly, 0, 0, 1000, 1000) == []
    assert check_village.onmap_field_edge(poly, 0, 0, 1000, 1000) == 0.0


def test_water_setback_scales_with_waterway_width():
    assert check_village.water_setback(4) == 75  # any small open water -> the floor (graves flood out)
    assert check_village.water_setback(9) == 75  # a narrow stream still gets the full floor
    assert check_village.water_setback(22) == 110  # moat -> moderate/large
    assert check_village.water_setback(40) == 140  # river / canal -> capped
    assert check_village.water_setback(9) < check_village.water_setback(22)  # wider water, more set-back


def test_matrix_survives_geometry_far_off_the_canvas():
    """A stray vertex must not make the overlap matrix allocate the world.

    `GridIndex.add` inserts under every cell an item's bbox touches, so ONE feature reaching far
    off-map costs a dict entry per 120 px in BOTH axes. The `city_geometry_within_canvas` fixture
    plants a wall vertex at 9,000,000 on a 3,200 px canvas - once `wall` was classified as a solid,
    that became ~5.6 BILLION cells and gigabytes of RAM, and the run had to be killed by hand
    (2026-07-26). The index box is now clamped to the canvas on BOTH insert and query - clamping
    only the insert leaves the query walking exactly the same cells.

    Timed rather than asserted structurally on purpose: the failure mode is unbounded work, and the
    margin here is enormous (well under a second when correct, effectively forever when not), so it
    is not a flaky threshold.
    """
    import time

    M = manifest(meta={"scale": "city", "ftpx": 3, "W": 3200, "H": 2700, "name": "Nowhere"})
    M["wall"] = [[100, 100], [3000, 100], [9000000, 9000000], [100, 2600], [100, 100]]
    # The stray wall vertex still yields quads that REACH the canvas, so it only exercises the
    # clamp. The second house is wholly off-map and exercises the skip on both the insert and the
    # query side - a feature nothing on the canvas can meet is not the overlap matrix's business.
    M["houses"] = [house(500, 500), house(50000, 50000)]
    t0 = time.time()
    check_village.matrix_violations(M)
    assert time.time() - t0 < 5.0, "the overlap matrix is walking cells for off-canvas geometry again - clamp the index box on BOTH insert and query"


def test_matrix_extracts_the_feature_020_linear_keys():
    """A record with no extents is invisible to every matrix check in both directions - feature
    019's blindness. The towpath records 'pts' and the aqueduct 'poly'; both must extract as
    STROKES via _MX_LINE_W (the aqueduct's open polyline must NOT fall through to the area-ring
    branch, which closes it into a sliver polygon)."""
    M = {"meta": {"scale": "capital"}, "towpaths": [{"pts": [[0, 0], [100, 0]], "w": 2.4}], "aqueducts": [{"poly": [[0, 50], [100, 50]], "w": 4.0, "intake": [0, 50], "to": [100, 50]}]}
    ks = [k for k, *_ in check_village.matrix_extents(M)]
    assert ks.count("towpaths") == 1 and ks.count("aqueducts") == 1
