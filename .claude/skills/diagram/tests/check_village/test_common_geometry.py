"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

import pytest

import check_village
import settlement
from tests.check_village._builders import _kiln_map, bldg, well


def test_seg_intersect_parallel_returns_none():
    assert check_village.seg_intersect((0, 0), (10, 0), (0, 5), (10, 5)) is None


def test_manor_rotation_records_rot_and_tilts_the_footprint():
    s = settlement.Settlement()
    s.manor(500, 500, 200, 120, "M", gate_dir="south", rot=30)
    mn = s.M["manors"][0]
    assert mn["rot"] == 30
    c = check_village.rect_corners(mn)
    assert abs(c[0][1] - c[1][1]) > 1  # the top edge is no longer horizontal -> the compound is tilted


def test_seg_to_rect_dist_zero_on_corner_touch_and_positive_when_apart():
    r = {"x": 100, "y": 100, "w": 40, "h": 20, "rot": 0}  # x 80..120, y 90..110
    assert check_village.seg_to_rect_dist((100, 60), (100, 200), r) == 0.0  # vertical segment crosses the rect
    assert check_village.seg_to_rect_dist((90, 100), (110, 100), r) == 0.0  # segment lies fully INSIDE (endpoint-in branch)
    assert check_village.seg_to_rect_dist((200, 100), (260, 100), r) > 0  # a segment well to the east


# ---- feature 006: defensive-branch coverage (empty pts, degenerate quarter) ----------------
def test_largest_empty_gap_is_infinite_with_no_points():
    assert check_village.largest_empty_gap([[0, 0], [10, 0], [10, 10], [0, 10]], []) == float("inf")


# ---- robustness: bounded sweeps + geometry sanity (2026-07-14, hang on malformed input) ----
def test_sweep_hi_clamps_a_runaway_bound_but_not_a_normal_one():
    assert check_village.sweep_hi(0, 3000, 8) == 3000  # a normal map span is untouched
    assert check_village.sweep_hi(0, 9_000_000, 8) == 8 * 500  # a runaway bound is clamped to cap*step


def test_kiln_quarters_carry_the_works_ROTATION():
    """A cottage is drawn inside the works' rotated group, so a record without the rotation puts a
    box at the right place with the wrong ORIENTATION. Both consumers read the same helper, and a
    four-element record predates the field and is read as rot=0 - which is what it was."""
    rotated = _kiln_map(rot=90.0)
    assert check_village.kiln_quarters(rotated["kilns"][0])[0]["rot"] == 90.0
    legacy = {"quarters": [[10.0, 20.0, 28.0, 18.0]]}  # a pre-2026-07-27 record, four elements
    assert check_village.kiln_quarters(legacy)[0]["rot"] == 0.0
    assert check_village.kiln_quarters({}) == []


def test_matrix_policy_resolves_every_pair_from_one_classification():
    """The point of the feature: no per-pair rules. A class decides everything."""
    assert check_village.matrix_policy("dry_plots", "streams") is None  # GROUND x WATER - the motivating defect
    assert check_village.matrix_policy("dry_plots", "road") is None  # GROUND x WAY
    assert check_village.matrix_policy("houses", "buildings") is None  # SOLID x SOLID
    assert check_village.matrix_policy("commons", "houses")  # COVER is permissive - the GM's own example
    assert check_village.matrix_policy("quarters", "houses")  # an overlay contains features
    assert check_village.matrix_policy("streams", "channels")  # confluence
    assert check_village.matrix_policy("road", "town_streets")  # junction
    assert check_village.matrix_policy("road", "streams")  # bridged crossing
    assert check_village.matrix_policy("religious", "shrines")  # one hall recorded under two keys
    assert check_village.matrix_policy("dry_plots", "dry_plots")  # adjacent hem plots share headlands
    assert check_village.matrix_policy("village_groves", "houses")  # canopy is the canopy contract's job
    assert check_village.matrix_policy("hawk_mews", "houses") == "unclassified"


def test_edge_gap_handles_a_wellhead_which_is_drawn_as_a_disc_not_a_rect():
    """A well records r/vr and NO w/h, so a gap helper that assumes rects raises KeyError rather
    than measuring anything. That shipped for one turn on 2026-07-27 and the pool scan called it
    clean, because a crashing gate prints no FAIL lines - the file's own 'a check that never RUNS
    looks exactly like a check that passes'."""
    hall = bldg(500, 500, w=100, h=40)
    assert check_village.edge_gap(well(500, 600), hall) == pytest.approx(600 - 500 - 20 - 12)
    assert check_village.edge_gap(hall, well(500, 600)) == pytest.approx(600 - 500 - 20 - 12)
    assert check_village.edge_gap(well(500, 500), well(500, 560)) == pytest.approx(60 - 12 - 12)
    assert check_village.edge_gap(well(500, 500), hall) == 0.0  # inside the hall's footprint
