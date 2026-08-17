"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import random

import pytest

from l7r.diagram import settlement
from l7r.diagram.settlement import Settlement


def test_kosatsuba_draws_a_location_marker_at_the_coarse_tiers():
    # GM 2026-07-24: at village (2 ft/px) and city (3 ft/px) grain the true 12x5 ft frame draws a
    # 2.5 px / 1.7 px sliver that reads as fence hardware, so the GLYPH floors at the long-axis
    # marker minimum with the 12:5 aspect preserved. The manifest keeps TRUE feet in w/h and the
    # drawn box in vw/vh; the drawn box is what is reserved against later placement.
    for ftpx in (2, 3):
        s = Settlement(1000, 1000, seed=1)
        s.meta(name="C", scale="city" if ftpx == 3 else "village", ftpx=ftpx)
        s.kosatsuba(500, 500)
        kb = s.M["kosatsuba"][0]
        assert (kb["w"], kb["h"]) == (12 / ftpx, 5 / ftpx)  # true size, unchanged
        assert kb["vw"] == settlement.KOSATSUBA_MARKER_MIN_PX  # floored on the long axis...
        assert kb["vh"] == round(settlement.KOSATSUBA_MARKER_MIN_PX * 5 / 12, 1)  # ...aspect preserved
        assert s.placed[-1] == pytest.approx((500, 500, settlement.KOSATSUBA_MARKER_MIN_PX, settlement.KOSATSUBA_MARKER_MIN_PX * 5 / 12))  # the DRAWN box is reserved
        assert f'width="{kb["vw"]:.1f}"' in s.top[-1]  # and drawn


def test_scope_seed_depends_only_on_seed_name_and_key():
    # It must NOT depend on the process (hashlib, not the salted built-in hash()) nor on anything
    # drawn before it - that independence is the whole mechanism.
    a = settlement.scope_seed(23, "pack", (100, 200, 300, 400))
    random.random()
    assert settlement.scope_seed(23, "pack", (100, 200, 300, 400)) == a
    assert settlement.scope_seed(24, "pack", (100, 200, 300, 400)) != a  # the map seed matters
    assert settlement.scope_seed(23, "rowpack", (100, 200, 300, 400)) != a  # the scope name matters
    assert settlement.scope_seed(23, "pack", (100, 200, 300, 401)) != a  # the key matters
    assert settlement.scope_seed(23, "pack", (100.04, 200, 300, 400)) == a  # ...but not below 0.1 px


# ------------------------------------------------------------------------------------------------
# Knob engine (feature 005, Phase 2b): seeded, independent, historically-typed layout variation.
# These are the FAILING-first tests for the shared machinery (Knob / knob_rng / register_knob /
# resolve_knob + the Settlement pin/resolve surface); the actual Family-A knob catalog lands in US1.
# ------------------------------------------------------------------------------------------------


def test_knob_rng_is_deterministic_and_stable():
    # SHA-256-derived (not hash()-derived, which is per-process salted): a fixed (seed, knob) always
    # yields the same stream, so a roll is reproducible across runs/processes.
    a = settlement.knob_rng(7, "cluster_position")
    b = settlement.knob_rng(7, "cluster_position")
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]


def test_knob_rng_independent_per_knob():
    # different knob names draw from different streams (independence, not a shared global sequence)
    a = settlement.knob_rng(7, "cluster_position")
    b = settlement.knob_rng(7, "lane_skeleton")
    assert a.random() != b.random()


def test_knob_roll_deterministic():
    k = settlement.Knob("t_shape", ["a", "b", "c", "d"], default="a")
    assert k.roll(42, {}) == k.roll(42, {})


def test_knob_roll_independent_across_knobs():
    # two knobs with identical value spaces do NOT move in lockstep across seeds
    k1 = settlement.Knob("t_one", list(range(20)), default=0)
    k2 = settlement.Knob("t_two", list(range(20)), default=0)
    assert any(k1.roll(s, {}) != k2.roll(s, {}) for s in range(30))


def test_knob_two_seeds_give_different_draws():
    k = settlement.Knob("t_pos", list(range(20)), default=0)
    assert len({k.roll(s, {}) for s in range(30)}) > 1


def test_knob_roll_excludes_typing_invalid():
    # only even values are historically valid in this context; the roll never returns an odd one
    k = settlement.Knob("t_even", [1, 2, 3, 4, 5, 6], default=2, typing_rule=lambda v, ctx: v % 2 == 0)
    assert all(k.roll(s, {}) % 2 == 0 for s in range(40))


def test_knob_empty_filtered_space_is_loud():
    # no value satisfies the rule -> a spec error, never a silent fallback
    k = settlement.Knob("t_none", [1, 3, 5], default=1, typing_rule=lambda v, ctx: v % 2 == 0)
    with pytest.raises(ValueError):
        k.roll(1, {})


def test_resolve_order_pinned_beats_roll_and_default():
    settlement.register_knob(settlement.Knob("t_res", ["a", "b", "c"], default="a"))
    assert settlement.resolve_knob("t_res", 1, {}, {"t_res": "b"}) == "b"  # pinned wins
    assert settlement.resolve_knob("t_res", 1, {}, {}, do_roll=False) == "a"  # default when roll opted out
    assert settlement.resolve_knob("t_res", 1, {}, {}) in ("a", "b", "c")  # else rolled


def test_resolve_pin_not_in_value_space_rejected():
    settlement.register_knob(settlement.Knob("t_pin", ["x", "y"], default="x"))
    with pytest.raises(ValueError):
        settlement.resolve_knob("t_pin", 1, {}, {"t_pin": "z"})


def test_resolve_pin_typing_violation_rejected():
    settlement.register_knob(settlement.Knob("t_pin2", ["dry", "wet"], default="dry", typing_rule=lambda v, ctx: not (v == "wet" and ctx.get("region") == "upland")))
    with pytest.raises(ValueError):
        settlement.resolve_knob("t_pin2", 1, {"region": "upland"}, {"t_pin2": "wet"})
    # the same pin is fine in a delta region
    assert settlement.resolve_knob("t_pin2", 1, {"region": "delta"}, {"t_pin2": "wet"}) == "wet"


def test_settlement_resolve_surface_records_and_feeds_context():
    s = Settlement(1000, 1000, seed=5)
    s.meta(name="V", scale="village", region="upland")
    settlement.register_knob(settlement.Knob("t_sk", ["p", "q"], default="p"))
    # a knob whose typing rule reads an EARLIER resolved knob from the running context
    settlement.register_knob(settlement.Knob("t_dep", ["lo", "hi"], default="lo", typing_rule=lambda v, ctx: not (v == "hi" and ctx.get("t_sk") == "p")))
    s.pin_knob("t_sk", "q")
    assert s.resolve("t_sk") == "q"
    assert s._resolved_knobs["t_sk"] == "q"
    # region flows from meta into the context; t_sk="q" so t_dep may be "hi"
    assert "region" in s.knob_context() and s.knob_context()["t_sk"] == "q"
    assert s.resolve("t_dep") in ("lo", "hi")


def test_settlement_resolve_default_when_unpinned_and_no_roll():
    s = Settlement(1000, 1000, seed=5)
    s.meta(name="V", scale="village")
    settlement.register_knob(settlement.Knob("t_def", ["one", "two"], default="one"))
    assert s.resolve("t_def", do_roll=False) == "one"


# ---- Family-A knob catalog (feature 005, US1): value spaces + China-first typing rules ----------


def test_family_a_knobs_are_registered_with_expected_value_spaces():
    for name, space in [
        ("cluster_position", {"high_margin", "flank", "mid_margin", "valley_mouth", "valley_head", "on_rise"}),
        ("cluster_shape", {"round", "elongated", "crescent", "split"}),
        ("lane_skeleton", {"spine", "T", "Y", "cross", "waterside"}),
        ("plot_size", {"small_irregular", "medium", "large_block", "strip"}),
        ("plot_regularity", {"organic", "grid"}),
    ]:
        assert set(settlement.KNOBS[name].value_space) == space


def test_lane_skeleton_waterside_typing():
    k = settlement.KNOBS["lane_skeleton"]
    assert "waterside" not in k.allowed({"water_kind": "pond"})  # pond-fed valley: no water alongside
    assert "waterside" in k.allowed({"water_kind": "stream"})  # stream-fed: a lane can hug the water
    assert "waterside" in k.allowed({"waterside_site": True})  # explicit canal/waterside site
    assert set(k.allowed({"water_kind": "pond"})) == {"spine", "T", "Y", "cross"}


def test_water_source_position_typing_pond_vs_stream():
    k = settlement.KNOBS["water_source_position"]
    pond = set(k.allowed({"water_kind": "pond"}))
    stream = set(k.allowed({"water_kind": "stream"}))
    assert pond == {"corner_NW", "corner_NE", "corner_SW", "corner_SE", "mid_margin", "chain"}
    assert stream == {"edge_N", "edge_E", "edge_S", "edge_W"}


def test_cluster_shape_split_needs_room():
    k = settlement.KNOBS["cluster_shape"]
    assert "split" not in k.allowed({"scale": "hamlet"})
    assert "split" in k.allowed({"scale": "village"})


def test_plot_regularity_grid_needs_planned_field():
    k = settlement.KNOBS["plot_regularity"]
    assert k.allowed({"field_origin": "organic"}) == ["organic"]  # old organically-grown field: no grid
    assert set(k.allowed({"field_origin": "planned"})) == {"organic", "grid"}


def test_family_a_roll_always_satisfies_typing_rule():
    # a pond-fed, organically-grown valley village (Kikuta/Hoshigaoka geography): every rolled knob value
    # is historically coherent for that context, across many seeds
    ctx = {"water_kind": "pond", "field_origin": "organic", "scale": "village"}
    for name in ("cluster_position", "cluster_shape", "lane_skeleton", "water_source_position", "plot_size", "plot_regularity", "grain_drift"):
        k = settlement.KNOBS[name]
        for seed in range(25):
            v = k.roll(seed, ctx)
            assert k.typing_rule(v, ctx)
            assert v != "waterside" and not str(v).startswith("edge_") and v != "grid"


def test_grain_drift_value_space():
    assert settlement.KNOBS["grain_drift"].value_space == [-12, -8, -4, 0, 4, 8, 12]


# ---- lane_skeleton knob: DERIVED headman/shrine placement (feature 005, US1) --------------------


def test_skeleton_layout_derives_distinct_headman_positions_per_skeleton():
    # the whole point: the headman position is DERIVED from the skeleton, so different skeletons put it in
    # different places (this is what stops two same-water villages from sharing a headman position)
    cx, cy, ex, ey = 400, 700, 120, 210
    hp = {k: settlement.skeleton_layout(k, cx, cy, ex, ey)["headman"] for k in settlement.LANE_SKELETONS}
    assert len(set(hp.values())) == len(hp)  # every skeleton's headman is a distinct point
    assert hp["spine"][1] < cy  # spine: at the high head (above center)
    assert hp["cross"] != (cx, cy) and settlement.skeleton_layout("cross", cx, cy, ex, ey)["market"] == (cx, cy)  # headman beside the market node
    assert hp["T"][1] < cy and hp["Y"][1] > cy  # T junction is upper, Y fork is lower
    assert hp["waterside"][0] < cx  # waterside: fronting the water flank (west of center)


def test_skeleton_layout_gateway_is_downslope_and_market_only_for_cross():
    for k in settlement.LANE_SKELETONS:
        lay = settlement.skeleton_layout(k, 400, 700, 120, 210)
        if k == "waterside":
            assert lay["gateway"][1] > 700  # foot of the waterside lane
        else:
            assert lay["gateway"] == (400, 910)  # downslope foot of the cluster
        assert ("market" in lay) == (k == "cross")  # only a cross yields a market node


def test_skeleton_layout_rejects_unknown_kind():
    import pytest

    with pytest.raises(ValueError):
        settlement.skeleton_layout("spiral", 0, 0, 10, 10)


def test_wall_tower_spacing_px_scales_with_tier():
    """The per-city defense tier sets the max mural-tower spacing. siege = aimed-lethal bowshot
    (197 ft), >=2 everywhere, so spacing == range; garrison = full war-bow (328 ft), >=2, so the
    wider range; peaceful keeps only >=1 flanking tower within aimed-lethal range, so its spacing
    is DOUBLE (a tower every 2*197 ft - the sparser Xi'an crossfire). At 3 ft/px (city scale):"""
    ppf = 1.0 / 3.0  # px per ft
    assert settlement.wall_tower_spacing_px(ppf, "siege") == 197.0 * ppf
    assert settlement.wall_tower_spacing_px(ppf, "garrison") == 328.0 * ppf
    assert settlement.wall_tower_spacing_px(ppf, "peaceful") == 2 * 197.0 * ppf
    # siege is tighter than garrison; peaceful is the loosest
    assert settlement.wall_tower_spacing_px(ppf, "siege") < settlement.wall_tower_spacing_px(ppf, "garrison")
    assert settlement.wall_tower_spacing_px(ppf, "peaceful") > settlement.wall_tower_spacing_px(ppf, "garrison")


def test_wall_tower_spacing_px_unknown_tier_falls_back_to_garrison():
    ppf = 1.0 / 3.0
    assert settlement.wall_tower_spacing_px(ppf, "nonsense") == settlement.wall_tower_spacing_px(ppf, "garrison")


def test_moat_current_and_swept_tap_degenerate_rings():
    # a "ring" of two points is not a ring: both helpers bail rather than index past the ends
    assert settlement.moat_current_at([(0, 0), (10, 0)], (0, 0), (10, 0), (5, 5)) is None
    assert settlement.moat_swept_tap([(0, 0), (10, 0)], (0, 0), (10, 0), (5, 5), (9, 9)) == (9, 9)


def test_moat_swept_tap_handles_a_zero_length_edge_and_an_unreachable_target():
    # a duplicated consecutive vertex gives a zero-length edge to step over; want_deg=-1 can never be
    # met, so the walk exhausts max_back and falls back to the best angle it saw
    ring = [(400, 300), (700, 300), (700, 300), (700, 700), (400, 700), (400, 300)]
    got = settlement.moat_swept_tap(ring, (400, 300), (700, 700), (250, 500), (400, 500), want_deg=-1.0, max_back=60.0)
    assert isinstance(got, tuple) and len(got) == 2


def test_moat_swept_tap_scores_a_zero_length_throat_as_unusable():
    # `other` sitting exactly on the candidate leaves no direction to measure - scored 999, never chosen
    ring = [(400, 300), (700, 300), (700, 700), (400, 700), (400, 300)]
    got = settlement.moat_swept_tap(ring, (400, 300), (700, 700), (400, 500), (400, 500), want_deg=-1.0, max_back=40.0)
    assert isinstance(got, tuple)


def test_sharp_corners_skips_a_duplicate_vertex_instead_of_counting_it():
    """A repeated vertex turns through no angle at all, so it is neither a hard corner nor an eased
    one - counting it either way would misreport the parcel-fabric shape the manifest records.

    Pinned by a test rather than by a generator accident: the comb used to emit quads with a
    collapsed 4th vertex at the fan's corner, which is what exercised this branch. `build_comb` now
    merges those away (a triangle is recorded as a triangle), so nothing in the pool reaches it -
    but the other field engines' rings can still carry one, and the guard is still right."""
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert settlement._sharp_corners(square) == 4
    # The same square with its last vertex repeated. The repeat is NOT counted as a fifth corner -
    # and note it costs the corner it duplicates as well, since that vertex's outgoing edge is now
    # zero-length and gets skipped too. So a ring carrying duplicates under-reports its corners,
    # which is exactly why `build_comb` merges them away instead of leaning on this guard.
    assert settlement._sharp_corners([*square, (0.0, 10.0)]) == 3
