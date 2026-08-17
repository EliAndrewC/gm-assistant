#!/usr/bin/env python3
"""Unit tests for site_justice.py - the justice-works siting tool.

The tool's whole claim is that it does not restate the gate's rules, so these tests check the
plumbing (footprints taken from settlement.py, trial records shaped like the engine's, frame cost
measured off crop_boxes, the ranking that keeps gate runs few) and that adjudication really is
`gate(trial) - gate(without)`. The rules themselves are tested in tests/check_village/, which is
the point: there is only one place they live.

    python3 -m pytest tests/tools/test_site_justice.py -q
"""

import json
import math

import pytest

from l7r.diagram import settlement
from l7r.diagram.tools import site_justice as sj

WALL = [[600, 600], [1400, 600], [1400, 1400], [600, 1400]]


def town(**over):
    """A minimal unwalled county seat that PASSES the justice checks once a ground is seated: a
    core on an east-west road, the burakumin quarter east of it, a stone beyond that, and the
    community's dead far to the north."""
    M = {
        "meta": {"scale": "town", "ftpx": 1, "W": 2400, "H": 2000},
        "road": [[100, 1000], [2300, 1000]],
        "houses": [{"x": 440 + 30 * i, "y": 940, "w": 46, "h": 28, "rot": 0, "kind": "plain"} for i in range(6)],
        "buildings": [{"x": 1000, "y": 1010, "w": 40, "h": 28, "rot": 0, "kind": "burakumin"}],
        "punishment_spots": [{"x": 520, "y": 1020, "w": 30, "h": 12, "rot": 0, "label": "punishment ground"}],
        "boundary_markers": [{"x": 1300, "y": 1020, "w": 3, "h": 3, "vw": 7, "vh": 7, "rot": 0, "label": "boundary stone"}],
        "cemeteries": [{"x": 1500, "y": 300, "w": 100, "h": 80, "rot": 0, "parish": False}],
    }
    M.update(over)
    return M


def city(**over):
    M = town(**over)
    M["meta"] = {**M["meta"], "scale": "city", "ftpx": 3}
    return M


# ---- footprints and trial records come from the ENGINE, not from numbers retyped here ----------
@pytest.mark.parametrize(
    ("kind", "maker", "expect"),
    [
        ("execution_ground", town, (60.0, 60.0)),
        ("execution_ground", city, (100 / 3, 60 / 3)),
        ("punishment_spot", town, (30.0, 12.0)),
    ],
)
def test_footprint_px_matches_the_engines_own_figures(kind, maker, expect):
    assert sj.footprint_px(maker(), kind) == pytest.approx(expect)


def test_boundary_marker_footprint_is_the_drawn_marker_box():
    # A real stone is ~3 ft - sub-glyph at every tier - so what can collide is the DRAWN box.
    assert sj.footprint_px(town(), "boundary_marker") == (settlement.BOUNDARY_MARKER_MIN_PX, settlement.BOUNDARY_MARKER_MIN_PX)


def test_record_carries_the_fields_each_kind_needs():
    eg = sj.record(town(), "execution_ground", 100, 200, rot=8)
    assert (eg["x"], eg["y"], eg["rot"], eg["screened"]) == (100.0, 200.0, 8, False)
    assert sj.record(city(), "execution_ground", 100, 200)["screened"] is True  # a city ground is hoarded
    bm = sj.record(town(), "boundary_marker", 100, 200)
    assert bm["w"] == bm["h"] == settlement.BOUNDARY_MARKER_FT  # TRUE footprint recorded...
    assert bm["vw"] == bm["vh"] == settlement.BOUNDARY_MARKER_MIN_PX  # ...alongside the drawn box


def test_with_replaces_only_the_one_registry():
    M = town()
    trial = sj._with(M, "execution_ground", [sj.record(M, "execution_ground", 1, 2)])
    assert len(trial["execution_grounds"]) == 1
    assert not M.get("execution_grounds")  # the caller's manifest is untouched
    assert trial["houses"] is M["houses"]  # and the rest is shared, not copied


# ---- adjudication is the real gate, differenced ------------------------------------------------
def test_new_failures_reports_only_what_the_placement_adds():
    M = town()
    base = sj.failures(sj._with(M, "execution_ground", []))
    assert "town_has_execution_ground" in base  # absent -> the presence check fires...
    good = sj.new_failures(M, "execution_ground", 1700, 1060, base)
    assert not good  # ...and seating it there adds nothing, so the presence failure is differenced out


def test_new_failures_surfaces_a_rule_the_tool_never_names():
    # Seated among the dwellings. The tool has no idea what this rule is called - it just reports
    # what the gate said - which is the entire design.
    M = town()
    base = sj.failures(sj._with(M, "execution_ground", []))
    assert "execution_ground_outside_the_settlement" in sj.new_failures(M, "execution_ground", 520, 1000, base)


# ---- frame arithmetic --------------------------------------------------------------------------
def test_view_box_prefers_the_recorded_view_and_falls_back_to_the_canvas():
    assert sj.view_box(town()) == (0.0, 0.0, 2400.0, 2000.0)
    M = town()
    M["meta"]["view"] = [100, 200, 300, 400]
    assert sj.view_box(M) == (100.0, 200.0, 400.0, 600.0)


def test_frame_cost_is_zero_inside_the_content_box_and_grows_outside_it():
    M = town()
    box = sj.content_box(M, "execution_ground")
    assert sj.frame_cost(M, "execution_ground", (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, box=box) == 0
    out = sj.frame_cost(M, "execution_ground", box[2] + 200, (box[1] + box[3]) / 2, box=box)
    assert out == pytest.approx(230.0)  # 200 past the edge + the ground's own half-width


def test_frame_cost_computes_its_own_box_when_not_given_one():
    M = town()
    assert sj.frame_cost(M, "execution_ground", 1200, 1000) == sj.frame_cost(M, "execution_ground", 1200, 1000, box=sj.content_box(M, "execution_ground"))


# ---- ranking signals ---------------------------------------------------------------------------
def test_routes_collects_every_kind_of_way():
    M = town(town_streets=[{"pts": [[0, 0], [10, 10]], "w": 26}], lanes=[{"pts": [[5, 5], [6, 6]], "w": 8}])
    assert len(sj.routes(M)) == 3  # the road + the street + the lane


def test_way_out_distance_measures_roads_gates_and_the_single_gate():
    assert sj.way_out_distance(town(), 500, 1040) == pytest.approx(40.0)
    assert sj.way_out_distance(town(gates=[[500, 1200]]), 500, 1150) == pytest.approx(50.0)
    assert sj.way_out_distance(town(gate=[500, 1300]), 500, 1250) == pytest.approx(50.0)


def test_way_out_distance_is_infinite_with_nothing_to_measure_to():
    M = town()
    del M["road"]
    assert sj.way_out_distance(M, 0, 0) == math.inf


def test_outside_the_wall_treats_an_unwalled_map_as_all_outside():
    assert sj.outside_the_wall(town(), 1000, 1000)
    assert not sj.outside_the_wall(town(wall=WALL), 1000, 1000)
    assert sj.outside_the_wall(town(wall=WALL), 100, 100)


def test_rank_key_puts_each_feature_on_its_own_side_of_the_wall():
    M = town(wall=WALL)
    box = sj.content_box(M, "execution_ground")
    inside, outside = (1000.0, 1000.0), (200.0, 200.0)
    assert sj.rank_key(M, "execution_ground", outside, box)[0] < sj.rank_key(M, "execution_ground", inside, box)[0]
    assert sj.rank_key(M, "punishment_spot", inside, box)[0] < sj.rank_key(M, "punishment_spot", outside, box)[0]


def test_rank_key_prefers_beside_the_way_out_over_on_it():
    # Ranking by nearest-to-the-road puts candidates in the carriageway first; the band does not.
    M = town()
    box = sj.content_box(M, "execution_ground")
    on_road, beside = (1700.0, 1000.0), (1700.0, 1050.0)
    assert sj.rank_key(M, "execution_ground", beside, box)[2] < sj.rank_key(M, "execution_ground", on_road, box)[2]


def test_candidates_grid_stays_inside_the_view_with_room_for_the_footprint():
    M = town()
    w, h = sj.footprint_px(M, "execution_ground")
    pts = sj.candidates(M, "execution_ground", 200.0)
    assert pts
    assert all(w <= x <= 2400 - w and h <= y <= 2000 - h for x, y in pts)


# ---- end to end --------------------------------------------------------------------------------
def test_propose_returns_only_seats_the_gate_accepts():
    seats = sj.propose(town(), "execution_ground", limit=12, step=120.0)
    assert seats
    M = town()
    base = sj.failures(sj._with(M, "execution_ground", []))
    for s in seats:
        assert not sj.new_failures(M, "execution_ground", s["x"], s["y"], base)


def test_propose_rejects_a_seat_that_leaves_the_features_own_check_failing():
    """The `curable` half of adjudication - the half whose absence shipped a bad map.

    A feature whose ABSENCE is itself a gate failure puts that check into `base`, so a seat which
    leaves it failing adds nothing NEW and scored as legal. That is how the tool recommended the
    seat that put Ubame's boundary stone among the west-end shops (GM, 2026-07-26)."""
    M = town(execution_grounds=[{"x": 1700, "y": 1060, "w": 60, "h": 60, "rot": 0, "screened": False, "label": "execution ground"}], boundary_markers=[])
    base = sj.failures(sj._with(M, "boundary_marker", []))
    assert "execution_ground_past_the_boundary_marker" in base  # failing because there is no stone
    among_the_houses = (620.0, 1000.0)  # on the road, between core and ground, 67 ft from a house
    assert not sj.new_failures(M, "boundary_marker", *among_the_houses, base)  # adds nothing NEW...
    seats = sj.propose(M, "boundary_marker", limit=40, step=120.0)
    assert seats
    for s in seats:  # ...yet every seat the tool returns actually CURES the check
        trial = sj._with(M, "boundary_marker", [sj.record(M, "boundary_marker", s["x"], s["y"])])
        assert "execution_ground_past_the_boundary_marker" not in sj.failures(trial)


def test_propose_finds_nothing_when_every_ranked_seat_is_illegal():
    # limit=1 with a step that lands the single best-ranked candidate on the road.
    assert sj.propose(town(), "execution_ground", limit=1, step=900.0) == []


def test_report_names_the_seats_it_found():
    out = sj.report(town(), "execution_ground", 12, None, step=120.0)
    assert "adjudicating" in out and "frame_cost" in out


def test_report_says_so_when_there_is_no_legal_seat():
    assert "no legal seat" in sj.report(town(), "execution_ground", 1, (0.0, 0.0))


def test_report_judges_a_stone_against_the_chosen_ground():
    # With a ground pinned, the stone is adjudicated against THAT ground rather than against
    # whatever the manifest happened to carry.
    out = sj.report(town(), "boundary_marker", 8, (1700.0, 1060.0), step=200.0)
    assert "boundary_marker" in out


# ---- CLI ---------------------------------------------------------------------------------------
def test_main_prints_usage_without_enough_arguments(capsys):
    assert sj.main([]) == 2
    assert "tools.site_justice" in capsys.readouterr().out


def test_main_rejects_an_unknown_kind(tmp_path, capsys):
    f = tmp_path / "m.json"
    f.write_text(json.dumps(town()))
    assert sj.main([str(f), "gallows"]) == 2
    assert "unknown kind" in capsys.readouterr().out


def test_main_reports_seats(tmp_path, capsys):
    f = tmp_path / "m.json"
    f.write_text(json.dumps(town()))
    assert sj.main([str(f), "execution_ground", "--limit=6", "--step=200"]) == 0
    assert "adjudicating" in capsys.readouterr().out


def test_main_accepts_a_pinned_ground(tmp_path, capsys):
    f = tmp_path / "m.json"
    f.write_text(json.dumps(town()))
    assert sj.main([str(f), "boundary_marker", "--limit=4", "--ground=1700,1060"]) == 0
    assert "adjudicating" in capsys.readouterr().out
