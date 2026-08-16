"""Split from test_checks.py by feature 025 - see tests/check_village/CLAUDE.md for the index."""

import json
import pathlib

import pytest

import check_village
import settlement
from tests.check_village._builders import (
    _CAP_GOV_CHECKS,
    _GAP_RATCHET,
    _HAZARDS,
    _POND_OUTLIER,
    _SHRINE_GRAVEYARD_GROUP,
    _cap_gov,
    _capital_manifest,
    _feature_022_manifest,
    _haz_base,
    _justice_town,
    _tv,
    bldg,
    bstone,
    exground,
    f,
    garden,
    grove,
    house,
    manifest,
    pspot,
    solid,
    vgrove,
    well,
    yard,
)


def test_fixture_builders_survive_every_check():
    """The builders above must produce records EVERY check can read without a KeyError - that is
    the whole point of them. If a check starts indexing a new required key, this fails here once
    instead of ambushing the next person who writes a test."""
    M = manifest(
        houses=[house(300, 300)],
        buildings=[bldg(600, 600)],
        threshing_yards=[yard(300, 340, of=(300, 300))],
        gardens=[garden(340, 300, of=(300, 300))],
        wells=[well(500, 500)],
        groves=[grove(260, 260, of=(300, 300))],
        village_groves=[vgrove([(700, 700), (800, 700), (800, 800), (700, 800)])],
        tree_crowns=[900, 900, 6],
        punishment_spots=[pspot(400, 500)],
        execution_grounds=[exground(880, 200)],
        boundary_markers=[bstone(700, 350)],
    )
    f(M)  # must not raise; which checks FAIL is irrelevant here - only that they all ran


def test_brook_from_drain_outfall_runs_off_edge():
    # a natural BROOK that STARTS at the field drain's outfall (frm=drain) and runs off the map edge is
    # valid - exercises the "drain" anchor kind (the akusui empties into a valley brook, water OUT).
    M = {
        "field_ditches": [{"poly": [[300, 600], [700, 600]], "role": "drain", "field": "f"}],
        "streams": [{"poly": [[700, 600], [1200, 850], [1815, 1120]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}, "w": 9}],
    }
    fails = f(M)
    assert "stream_source_anchored[0]" not in fails and "stream_runs_off_edge[0]" not in fails


def test_stream_diverted_into_a_channel_passes_and_open_ended_brook_fires():
    # a BROOK flowing in from the top edge and artificially DIVERTED into the head-race at the field head
    # (frm=offmap, no `to`) is valid: it hands off to the irrigation net rather than running on over the
    # paddies. Exercises the at_ditch allowance - one end at the edge, the other ON an irrigation ditch.
    diverted = {
        "meta": {"W": 1000, "H": 1000},
        "field_ditches": [{"poly": [[500, 300], [500, 700]], "role": "main", "field": "f"}],
        "streams": [{"poly": [[500, 8], [500, 160], [500, 300]], "frm": {"kind": "offmap"}}],
    }
    assert "stream_runs_off_edge[0]" not in f(diverted)
    # TEETH: the same brook ending in OPEN ground (no edge/ditch/field/pond/moat/drain at its foot) must FIRE.
    open_ended = {"meta": {"W": 1000, "H": 1000}, "streams": [{"poly": [[500, 8], [500, 160], [500, 500]], "frm": {"kind": "offmap"}}]}
    assert "stream_runs_off_edge[0]" in f(open_ended)


# ---- module-level helper branches (direct calls) ------------------------------------------
def test_helper_edge_branches():
    cv = check_village
    assert cv.sat_overlap([(0, 0), (10, 0), (10, 10), (0, 10)], [(5, 5), (15, 5), (15, 15), (5, 15)])
    assert not cv.sat_overlap([(0, 0), (10, 0), (10, 10), (0, 10)], [(20, 20), (30, 20), (30, 30), (20, 30)])
    assert cv.seg_closest(0, 0, (5, 5), (5, 5)) == (5, 5)  # degenerate (zero-length) segment
    assert cv.unit_dir(None) is None  # no slope declared
    assert cv.unit_dir("nonsense") is None  # unknown cardinal name
    assert cv.unit_dir([3, 4]) == (0.6, 0.8)  # raw vector, normalized
    assert cv.poly_dist(5, 5, [(0, 0), (10, 0), (10, 10), (0, 10)]) == 0.0  # point inside the polygon


def test_gate_crop_advisory_is_soft_not_a_failure():
    fails = check_village.gate(_POND_OUTLIER, verbose=True)  # prints the ADVISORY line but must NOT gate the map
    assert "crop_could_tighten" not in fails


def test_gate_prints_the_group_advisory_phrasing():
    # the verbose gate line phrases a GROUP differently from a lone feature ("a N-feature group, moved as one unit")
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fails = check_village.gate(_SHRINE_GRAVEYARD_GROUP, verbose=True)
    out = buf.getvalue()
    assert "shrine+churchyard" in out and "group, moved as one unit" in out
    assert "crop_could_tighten" not in fails  # still a SOFT advisory, never a gate failure


def test_seg_intersect_returns_point_for_a_crossing_and_none_for_parallel():
    # the geometry helper that bridges() uses to find the crossing point
    p = settlement.seg_intersect((0, 0), (10, 0), (5, -5), (5, 5))
    assert p == (5.0, 0.0)
    assert settlement.seg_intersect((0, 0), (10, 0), (0, 4), (10, 4)) is None  # parallel - no crossing
    assert settlement.segments_cross((0, 0), (10, 0), (5, -5), (5, 5))
    assert not settlement.segments_cross((0, 0), (10, 0), (0, 4), (10, 4))


def test_mausoleum_draws_with_either_gate_orientation():
    # exercises both the horizontal-wall (south) and vertical-wall (west) gate branches + the default
    # (above) label position
    s = settlement.Settlement()
    s.mausoleum(900, 900, 120, 90, label="Mausoleum", gate_dir="south")
    s.mausoleum(600, 600, 120, 90, gate_dir="west")
    assert len(s.M["mausoleums"]) == 2


def test_twin_detector_fires_on_twinned_pair():
    # two structurally-identical villages (the Kikuta/Hoshigaoka situation) -> zero axes differ -> TWINNED
    rep = check_village.twin_report([_tv(meta={"name": "A"}), _tv(meta={"name": "B"})])
    assert len(rep) == 1
    assert rep[0]["verdict"] == "TWINNED" and rep[0]["diffs"] == 0 and rep[0]["pair"] == ("A", "B")


def test_twin_detector_passes_distinct_pair():
    a = _tv(meta={"name": "A", "cluster_shape": "round", "lane_skeleton": "spine", "water_source_position": "corner_NW", "focal_features": []})
    b = _tv(meta={"name": "B", "cluster_shape": "crescent", "lane_skeleton": "cross", "water_source_position": "chain", "focal_features": ["mill"]})
    rep = check_village.twin_report([a, b])
    assert len(rep) == 1 and rep[0]["verdict"] == "PASS" and rep[0]["diffs"] >= 4


def test_twin_detector_skips_different_or_missing_down_deg():
    a = _tv(meta={"name": "A", "down_deg": 45})
    b = _tv(meta={"name": "B", "down_deg": 135})
    c = _tv(meta={"name": "C"})
    c["meta"].pop("down_deg")
    assert check_village.twin_report([a, b]) == []  # different water direction -> not compared
    assert check_village.twin_report([a, c]) == []  # one map lacks down_deg -> not compared


def test_twin_axes_geometric_fallbacks_no_meta_knobs():
    ax = check_village.twin_axes(_tv(meta={"name": "G"}))
    assert ax["cluster_region"] == "W"  # cluster sits W of the field center
    assert ax["cluster_shape"] == "tall"  # bbox 60 wide x 140 tall -> r < 0.7
    assert ax["headman_side"] == "N"  # headman N of the cluster centroid
    assert ax["water_source"] == "NW"  # pond NW of the field center
    assert ax["lane_skeleton"] is None  # no declared knob, no geometric fallback
    assert ax["focal_set"] == frozenset()
    assert isinstance(ax["grain_orient"], int)


def test_twin_axes_round_cluster_center_headman_and_dir8_deadzone():
    # a square cluster CENTERED on the field center: round shape, headman AT the centroid (center),
    # and cluster_region hits _dir8's zero-vector dead zone -> None
    houses = [
        {"x": 300, "y": 300, "role": "plain"},
        {"x": 400, "y": 300, "role": "plain"},
        {"x": 300, "y": 400, "role": "plain"},
        {"x": 400, "y": 400, "role": "plain"},
        {"x": 350, "y": 350, "role": "headman"},
    ]
    ax = check_village.twin_axes({"meta": {"name": "R", "down_deg": 45}, "houses": houses, "fields": [{"bbox": [0, 0, 700, 700]}]})
    assert ax["cluster_shape"] == "round"  # w == h
    assert ax["headman_side"] == "center"  # headman at the cluster center
    assert ax["cluster_region"] is None  # centroid == field center -> dead zone
    assert ax["water_source"] is None and ax["grain_orient"] is None  # no pond, no dry_plots


def test_twin_axes_wide_cluster_and_bare_manifest():
    wide = [{"x": 100, "y": 300, "role": "plain"}, {"x": 500, "y": 300, "role": "plain"}, {"x": 300, "y": 320, "role": "plain"}]
    axw = check_village.twin_axes({"meta": {"name": "W", "down_deg": 45}, "houses": wide, "fields": [{"bbox": [0, 0, 700, 700]}]})
    assert axw["cluster_shape"] == "wide"  # 400 wide x 20 tall -> r > 1.4
    # a bare manifest: every geometric axis is 'no evidence'
    ax = check_village.twin_axes({"meta": {"name": "bare", "down_deg": 45}})
    assert ax["cluster_region"] is None and ax["cluster_shape"] is None and ax["headman_side"] is None
    assert ax["water_source"] is None and ax["grain_orient"] is None and ax["focal_set"] == frozenset()


def test_twin_axes_pond_layout_distinguishes_mosaic_from_grid():
    # GM 2026-07-22: a mosaic dike-pond (桑基魚塘) and a surveyed grid polder (圩田) of the same water
    # direction are different KINDS of place; pond_layout is a twin axis so the detector counts the difference.
    assert "pond_layout" in check_village.TWIN_AXES
    assert check_village.twin_axes({"meta": {"name": "G", "down_deg": 45}})["pond_layout"] == "grid"  # default
    assert check_village.twin_axes({"meta": {"name": "M", "down_deg": 45, "pond_layout": "mosaic"}})["pond_layout"] == "mosaic"
    grid = check_village.twin_axes({"meta": {"name": "G", "down_deg": 45, "field_archetype": "polder_grid"}})
    mosaic = check_village.twin_axes({"meta": {"name": "M", "down_deg": 45, "pond_layout": "mosaic"}})
    assert check_village.twin_diff_count(grid, mosaic) >= 1  # they differ on at least the pond_layout axis


def test_twin_report_none_axes_are_no_evidence_not_a_diff():
    # a fully-featured map vs a bare one: the bare map's None axes must NOT count as differences (a data
    # gap cannot manufacture distinctiveness) -> the pair stays TWINNED, not spuriously PASS
    rep = check_village.twin_report([_tv(meta={"name": "A"}), {"meta": {"name": "B", "down_deg": 45}}])
    assert len(rep) == 1 and rep[0]["verdict"] == "TWINNED"


def test_twin_report_uses_index_when_unnamed():
    rep = check_village.twin_report([{"meta": {"down_deg": 45}}, {"meta": {"down_deg": 45}}])
    assert rep and rep[0]["pair"] == ("0", "1")


def test_twin_settlement_form_is_an_axis():
    # nucleated blob vs linear ribbon - the biggest structural read - is a twin-detector axis; it defaults
    # to 'nucleated' when a map does not declare it (so an undeclared map is not spuriously "different")
    assert "settlement_form" in check_village.TWIN_AXES
    a = _tv(meta={"name": "A", "settlement_form": "nucleated"})
    b = _tv(meta={"name": "B", "settlement_form": "linear"})
    ax, bx = check_village.twin_axes(a), check_village.twin_axes(b)
    assert ax["settlement_form"] == "nucleated" and bx["settlement_form"] == "linear"
    assert check_village.twin_axes(_tv(meta={"name": "C"}))["settlement_form"] == "nucleated"  # default
    assert check_village.twin_diff_count(ax, bx) == 1  # differ on settlement_form alone (otherwise identical)


def test_convex_hull_degenerate_point_clouds():
    """The hull helper returns <3 unique points as-is (a degenerate, zero-area hull) - the guard the pool
    maps never reach (the compactness check needs >=12 houses) but that must not crash on a stray call."""
    import check_village as cv

    assert cv.convex_hull([]) == []
    assert cv.convex_hull([(1.0, 2.0)]) == [(1.0, 2.0)]
    assert cv.convex_hull([(1.0, 2.0), (3.0, 4.0), (1.0, 2.0)]) == [(1.0, 2.0), (3.0, 4.0)]  # 2 unique
    assert cv.poly_area(cv.convex_hull([(0.0, 0.0), (1.0, 1.0)])) == 0.0


def test_justice_town_fixture_passes_every_justice_check():
    # The control. Without it, a check that fires on EVERYTHING would look like a working check.
    bad = f(_justice_town())
    assert not {n for n in bad if n.startswith(("punishment_spot", "execution_ground", "town_has_punishment", "town_has_execution"))}


@pytest.mark.parametrize("hazard,expect,where,build,exempt", _HAZARDS, ids=[h[0].replace(" ", "_").replace("'", "") for h in _HAZARDS])
def test_every_solid_struct_is_gated_off_every_hazard(hazard, expect, where, build, exempt):
    missed = []
    for key in check_village._OVERLAP_STRUCTS:
        if key in exempt:
            continue
        M = _haz_base()
        M.update(build())
        M.setdefault(key, []).append(solid(key, *where))
        if expect not in f(M):
            missed.append(key)
    assert not missed, (
        f"{missed} sit on {hazard} without tripping {expect} - every _OVERLAP_STRUCTS key must be gated off every "
        f"hazard. The check is probably reading a hand-written list of manifest keys instead of solid_structs(M)."
    )


def test_the_new_trade_works_are_classified_in_both_registries():
    """The KEEP-CLEAR CONTRACT: registry membership alone gates a feature off every hazard and
    protects it from foreign captions. The border LINE is the deliberate exception - it is a line
    of law with no footprint, so it is exempt on both sides."""
    for key in ("charcoal_yards", "refining_forges"):
        assert key in check_village._OVERLAP_STRUCTS, key
        assert key in check_village._LABEL_GROUP, key
    assert "borders" in check_village._OVERLAP_EXEMPT
    assert "borders" in check_village._LABEL_EXEMPT


def test_a_border_line_under_a_compound_wall_trips_nothing():
    """A frontier magistracy stands its wall ON the line so the border runs across the parley-room
    floor (the Mode A ubame-magistracy sheet). Being overlapped is the arrangement, not a defect."""
    M = manifest(meta={"scale": "town", "ftpx": 1, "W": 1000, "H": 1000})
    M["borders"] = [{"poly": [[900, 0], [900, 1000]], "label": "the Fox border"}]
    M["manors"] = [{"x": 900, "y": 400, "w": 250, "h": 180, "rot": 0, "label": "Magistrate's Manor"}]
    assert not [c for c in f(M) if "border" in c]


@pytest.mark.parametrize(("name", "build", "offset", "must_fire", "why"), _GAP_RATCHET, ids=[r[0] for r in _GAP_RATCHET])
def test_gap_verdicts_read_footprints_not_centers(name, build, offset, must_fire, why):
    fired = name in f(build(offset))
    assert fired == must_fire, f"{name}: expected {'a failure' if must_fire else 'no failure'} at the disagreement offset ({why}) - this check is measuring centers or circumscribed radii again"


def test_capital_government_ward_checks_pass_on_the_full_fixture():
    fails = f(_cap_gov())
    for c in _CAP_GOV_CHECKS:
        assert c not in fails, c


def test_capital_packed_overflow_names_the_wall_resize_cure(capsys):
    """The in-wall-short + suburb-over combination must say, in so many words, that the wall
    must be resized - not merely that a band is off (the error message is the institutional
    memory here)."""
    M = _capital_manifest()
    M["meta"]["budget"]["dwelling_target"] = {"packed": 100, "packed_suburb": 30, "samurai_yashiki": 0, "samurai_detached": 0, "samurai_terrace": 0}
    M["districts"] = [
        {"name": "in machi", "kind": "machi", "poly": [[100, 100], [900, 100], [900, 900], [100, 900]]},
        {"name": "out ward", "kind": "machi", "poly": [[1200, 100], [1600, 100], [1600, 900], [1200, 900]]},
    ]

    def _pk(n, x0):
        return [{"kind": "laborer", "x": x0 + 14 * (i % 20), "y": 120 + 14 * (i // 20), "w": 10, "h": 7} for i in range(n)]

    M["buildings"] = _pk(40, 120) + _pk(60, 1220)
    import check_village

    check_village.gate(M, verbose=True)
    out = capsys.readouterr().out
    assert "CANNOT WORK WITHOUT RESIZING THE WALL" in out


def test_cistern_wells_with_no_aqueduct_fire():
    """A josui-ido cistern-well claims to draw on a buried main - with NO aqueduct on the map
    there is nothing to tap (coverage: the no-aqueduct branch)."""
    M = {"meta": {"scale": "town"}, "wells": [{"x": 500, "y": 500, "kind": "cistern"}]}
    assert any("cistern" in c for c in f(M)), "the no-aqueduct cistern must fail the josui-ido rule"


def test_feature_022_gate_refuses_an_unknown_check_name():
    with pytest.raises(ValueError, match="no_such_check_anywhere"):
        check_village.gate(_feature_022_manifest(), verbose=False, only={"no_such_check_anywhere"})


def test_feature_022_registry_base_names_match_the_frozen_legacy_set():
    frozen = json.loads((pathlib.Path(__file__).parent.parent / "fixtures" / "gate_check_names.json").read_text())
    registry = sorted({c for seg in check_village.GATE_SEGMENTS for c in seg.checks})
    assert registry == frozen
