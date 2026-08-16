"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import math

import pytest

import settlement
from settlement import Settlement, seg_dist
from tests.settlement._builders import _assert_no_glyph_overlaps, _cap020, _city, _crop_settlement, _town


def test_granary_draws_a_storehouse_row():
    # opt-in rice-transit granary: a row of n fireproof kura, recorded for town_has_granary
    s = _town()
    stores = s.granary(500, 500, n=3)
    assert len(stores) == 3 and s.M["granary"]["n"] == 3 and s.M["granary"]["label"] == "granary"


def test_cemetery_default_is_a_ruled_rectangle():
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70)
    assert 'width="100"' in s.out[-1] and "<path" not in s.out[-1]  # a plotted rectangle, no organic blob


def test_cemetery_organic_draws_an_irregular_plot():
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70, parish=False, organic=True)
    frag = s.out[-1]
    assert "<path" in frag and 'width="100"' not in frag  # a jittered blob outline, no ruled 100-wide plot rect
    assert s.M["cemeteries"][-1]["w"] == 100  # recorded bbox is still the w x h rectangle
    assert s.block_polys[-1] == [(242, 257), (358, 257), (358, 343), (242, 343)]  # no-build block unchanged (checks unaffected)


def test_cemetery_common_ground_defaults_organic():
    # organic derives from parish: a non-parish COMMON ground is Japan-style organic unless overridden
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70, parish=False)
    assert "<path" in s.out[-1] and 'width="100"' not in s.out[-1]


def test_cemetery_organic_false_keeps_the_louzeyuan_rectangle():
    # the deliberate per-city override: a plotted Chinese-style charity ground stays a ruled rectangle
    s = _crop_settlement()
    s.cemetery(300, 300, 100, 70, parish=False, organic=False)
    assert 'width="100"' in s.out[-1] and "<path" not in s.out[-1]


def test_animal_ground_records_a_yard_and_optional_label():
    # the city_no_large_empty_space remedy: a standalone stable-yard scatter claiming a pocket
    s = _crop_settlement()
    s.animal_ground(400, 400, r=60)  # no label - the rails and animals read on their own
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert (yd["x"], yd["y"], yd["r"], yd["of"], yd["troughs"]) == (400, 400, 60, [400, 400], 2)
    assert "troughs_at" in yd  # the cluster anchor stable_troughs_beside_well validates
    s.animal_ground(700, 700, r=52, label="caravan ground")
    s.flush_stable_yards()
    assert s.M["labels"][-1][5] == "caravan ground"  # label boxes are [x0, y0, x1, y1, z, text]


def test_caravan_scale_yard_gets_three_troughs_beside_the_nearest_well():
    # the watering point (settlements.md 'Stable yard' watering): a caravan-scale ground (r >= 76)
    # draws 3 troughs, and the cluster HUGS the recorded well - a bucket-pour from the wellhead
    # (GM 2026-07-23: "otherwise you'd have to carry the water a long way"), even a well past the rim
    s = _crop_settlement()
    s.M["wells"] = [{"x": 500, "y": 400, "r": 8, "vr": 4.0, "shrine": False}]
    s.animal_ground(400, 400, r=80)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["troughs"] == 3
    assert yd["troughs_at"] == [492.2, 400.0]  # wellhead vr 4.0 + half a 4.6 trough + 1.5 step from the well at x=500
    out = "".join(s.out)
    assert out.count('fill="#8FA6B0"') == 3  # the trough rects
    assert 'x="489.9"' in out  # the cluster's trough rects, centered on troughs_at


def test_vertical_hug_offsets_far_enough_to_clear_the_well_house_roof():
    # the Tango caravan-ground defect (GM 2026-07-23): a 3-trough stack is TALLER than it is
    # wide, so the old fixed offset (vr + half a trough LENGTH) let a near-vertical ray clip
    # the roof corner - the direction-aware offset clears the roof square along any ray
    s = _crop_settlement()
    s.M["wells"] = [{"x": 400, "y": 330, "r": 8, "vr": 4.0, "shrine": False}]  # due north: a vertical ray
    s.animal_ground(400, 400, r=80)  # caravan scale - 3 troughs
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["troughs"] == 3
    bx0, by0, bx1, by1 = yd["troughs_box"]
    assert by0 >= 330 + 4.0  # the box top clears the roof square's bottom edge
    assert by0 - (330 + 4.0) == pytest.approx(1.5, abs=0.11)  # ... by exactly the bucket-pour step (round-off)


def test_cluster_walks_off_a_neighbor_wells_roof():
    # an idobata PAIR: the yard sits on well A (dist < 1, skipped as the target), so the cluster
    # hugs well B - but B's yard-side flank lands on A's roof, so the walk-around must find a
    # flank clear of BOTH roofs (the neighbor-well rejection)
    s = _crop_settlement()
    s.M["wells"] = [
        {"x": 400, "y": 400, "r": 8, "vr": 4.0, "shrine": False},  # A - under the yard center
        {"x": 408, "y": 400, "r": 8, "vr": 4.0, "shrine": False},  # B - the target
    ]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    bx0, by0, bx1, by1 = s.M["stable_yards"][-1]["troughs_box"]
    for w in s.M["wells"]:
        vr = w["vr"]
        assert not (bx0 < w["x"] + vr and bx1 > w["x"] - vr and by0 < w["y"] + vr and by1 > w["y"] - vr)


def test_yard_digs_its_own_well_when_the_near_wellheads_flanks_are_all_blocked():
    # the Nagahara yard-1 case: a well IS in reach, but a building crowds every flank of the
    # wellhead, so no bucket-pour spot exists beside it - the yard digs its own well instead
    s = _crop_settlement()
    s.M["wells"] = [{"x": 400, "y": 460, "r": 8, "vr": 4.0, "shrine": False}]
    s.M["buildings"] = [{"x": 400, "y": 460, "w": 40, "h": 40}]  # covers the whole flank ring
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    assert len(s.M["wells"]) == 2  # the in-reach well was unusable; the yard dug its own
    nw, ta = s.M["wells"][-1], s.M["stable_yards"][-1]["troughs_at"]
    assert math.hypot(nw["x"] - ta[0], nw["y"] - ta[1]) <= s.px(40)  # cluster hugs the new wellhead


def test_yard_digs_its_own_well_when_none_in_reach():
    # every recorded well beyond r + 40: the yard sinks its OWN courtyard well and clusters the
    # troughs beside it (the caravanserai / yizhan post-yard form - GM 2026-07-23, the Nagahara
    # defect: the old fallback dropped the cluster at a random spot, a 100-241 ft bucket-carry)
    s = _crop_settlement()
    s.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["troughs"] == 2
    assert len(s.M["wells"]) == 2  # the yard dug its own
    nw = s.M["wells"][-1]
    assert math.hypot(nw["x"] - 400, nw["y"] - 400) <= 60  # sunk inside the yard disc
    ta = yd["troughs_at"]
    assert math.hypot(nw["x"] - ta[0], nw["y"] - ta[1]) <= s.px(40)  # cluster hugs the new wellhead


def test_hitching_rails_refuse_a_seat_across_a_wellhead():
    # the GM-caught Nagahara defect (2026-07-25): a rail drawn straight over a wellhead. The yard's
    # RNG is seeded on its own position, so the seats it takes are deterministic - draw the yard
    # once to learn where its rails land, then sink a wellhead on each of those exact spots. Before
    # the rule, `clear()` knew nothing about wells and the second yard drew the identical rails,
    # straight across all three heads; now it must walk to clear ground instead.
    bare = _crop_settlement()
    bare.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]  # out of reach, so nothing near the yard
    bare.animal_ground(400, 400, r=60)
    bare.flush_stable_yards()
    seats = [(rl["x"], rl["y"]) for rl in bare.M["stable_yards"][-1]["rails"]]
    assert len(seats) == 2  # the two interior rails (no road in this bare fixture, so no road-parallel rail)

    s = _crop_settlement()
    s.M["wells"] = [{"x": sx, "y": sy, "r": 8, "vr": 4.0, "shrine": False} for sx, sy in seats]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["rails"]  # the train still ties up somewhere - the rule moves rails, it does not delete them
    assert [(rl["x"], rl["y"]) for rl in yd["rails"]] != seats  # ... and they are NOT the old on-the-wellhead seats
    _assert_no_glyph_overlaps(s)


def test_the_trough_cluster_walks_off_a_rail_already_seated():
    # the other half of the Nagahara defect: the watering point is placed AFTER the rails, and it is
    # PINNED - it must hug its well - so it is the side that has to walk. Sink the well 10.5px
    # beyond a known rail seat, off the rail itself but close enough that the natural yard-side
    # flank (well + ~8px bucket-pour offset) lands the cluster squarely on the rail. Before the
    # rule, beside() knew nothing about rails and stacked the troughs on the posts.
    bare = _crop_settlement()
    bare.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]  # out of reach: nothing near the yard
    bare.animal_ground(400, 400, r=60)
    bare.flush_stable_yards()
    sx, sy = [(rl["x"], rl["y"]) for rl in bare.M["stable_yards"][-1]["rails"]][0]  # a horizontal rail north of the yard center

    s = _crop_settlement()
    s.M["wells"] = [{"x": sx, "y": sy - 10.5, "r": 8, "vr": 4.0, "shrine": False}]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["troughs"] == 2 and yd["rails"]  # the yard still waters its train and still ties it up
    _assert_no_glyph_overlaps(s)


def test_a_yard_digs_its_own_well_clear_of_its_own_rails():
    # the dig-your-own-well fallback draws a THIRD glyph after the rails are down, so it predicts
    # its own head size (_well_vr) and seats clear of them
    s = _crop_settlement()
    s.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]  # far out of reach: the yard sinks its own
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert len(s.M["wells"]) == 2 and yd["troughs"] == 2 and yd["rails"]
    _assert_no_glyph_overlaps(s)


def test_a_rail_refuses_a_seat_on_an_EARLIER_yards_trough_cluster():
    # the cross-yard branch, reached by CONSTRUCTION since no natural yard spacing produces it (see
    # the preventive-guard test below): a neighboring yard just north has already put its watering
    # point at our yard's first rail seat, so that seat must be refused and the rail retried
    bare = _crop_settlement()
    bare.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]
    bare.animal_ground(400, 400, r=60)
    bare.flush_stable_yards()
    sx, sy = [(rl["x"], rl["y"]) for rl in bare.M["stable_yards"][-1]["rails"]][0]

    s = _crop_settlement()
    s.M["wells"] = [{"x": 900, "y": 900, "r": 8, "vr": 4.0, "shrine": False}]
    s.M["stable_yards"] = [
        {"x": 400, "y": 340, "r": 40.0, "of": [400, 340], "troughs": 2, "troughs_at": [sx, sy], "troughs_box": [sx - 2.3, sy - 2.8, sx + 2.3, sy + 2.8], "rails": [], "dung_heaps": []}
    ]
    s.animal_ground(400, 400, r=60)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["rails"] and (sx, sy) not in [(rl["x"], rl["y"]) for rl in yd["rails"]]  # seat refused, rail retried elsewhere
    _assert_no_glyph_overlaps(s)


def test_a_second_yards_furniture_keeps_off_the_first_yards_glyphs():
    # PREVENTIVE guard, not a reproduction: no natural two-yard spacing yet produces a cross-yard
    # collision (searched the 90-150px x 0-90px offset grid at three yard radii, 2026-07-25), but
    # each yard still measures against every EARLIER yard's rails and cluster - the dung-heap rule
    # shipped without that and had to be widened for exactly this hole twice. The check is what
    # actually catches it, from whatever direction it arrives; this holds the placement side honest.
    s = _crop_settlement()
    s.M["wells"] = [{"x": 460, "y": 400, "r": 8, "vr": 4.0, "shrine": False}]  # in reach of BOTH yards
    s.animal_ground(400, 400, r=60)
    s.animal_ground(520, 400, r=60)
    s.flush_stable_yards()
    assert len(s.M["stable_yards"]) == 2
    _assert_no_glyph_overlaps(s)


# --- merchant_residences(): rich homes derived from the ACTUAL shops, behind the storefront band ---
def test_merchant_residences_returns_zero_without_a_road_or_shops():
    s = Settlement(1000, 1000, seed=1)
    assert s.merchant_residences() == 0  # no road, no shops
    s.road([(50, 500), (950, 500)])
    assert s.merchant_residences() == 0  # a road but still no shops


def test_stable_yard_scatter_keeps_off_the_farriers_forge():
    # the farrier is the one trade work sited INSIDE a stable yard, so it must be in the yard's
    # keep-out set - otherwise the scatter speckles straw litter across the forge and its apron.
    s = _city()
    s.farrier(660, 620)
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    fr = s.M["farriers"][-1]
    yd = s.M["stable_yards"][-1]
    hw, hh = fr["w"] / 2 + 3, fr["h"] / 2 + 3
    for key in ("rails", "dung_heaps"):
        for o in yd.get(key) or []:
            assert not (abs(o["x"] - fr["x"]) < hw and abs(o["y"] - fr["y"]) < hh), f"{key} on the forge"


def test_stables_draws_a_working_yard_and_records_it():
    # the gate stables' beaten-earth yard (GM 2026-07-22): drawing it adds scatter/furniture to the
    # SVG and records a stable_yard linked to the stables, so stables_have_yards can gate it. The yard
    # scatter avoids a neighboring building (an inn placed just north).
    s = _city()
    s.inn(600, 540)  # a cluster building the yard must skip
    before = len(s.out)
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    assert len(s.out) > before  # the yard scatter + furniture drew something
    yd = s.M["stable_yards"][-1]
    assert yd["of"] == [600.0, 620.0] and yd["r"] > 0
    # nothing the yard drew lands on the inn's footprint (a 3px-margin keep-out)
    ix0, iy0, ix1, iy1 = 600 - s.M["buildings"][0]["w"] / 2, 540 - s.M["buildings"][0]["h"] / 2, 600 + s.M["buildings"][0]["w"] / 2, 540 + s.M["buildings"][0]["h"] / 2
    assert ix1 > ix0 and iy1 > iy0  # sanity: the inn has a real footprint the scatter avoided


def test_stables_yard_can_be_suppressed():
    s = _city()
    s.stables(600, 620, rot=90, yard=False)
    s.flush_stable_yards()
    assert not s.M.get("stable_yards")  # yard=False draws no yard


def test_stables_yard_fully_blocked_draws_no_furniture():
    # a yard whose whole disk is covered by a field: every scatter/furniture candidate is rejected
    # (the field-reject branch), take() exhausts, and the cart/dung loops break - the yard is still
    # recorded (so stables_have_yards passes) but no beaten-earth furniture is drawn
    s = _city()
    s.field_polys.append([(400, 400), (800, 400), (800, 840), (400, 840)])  # blankets the r=72 disk at (600,620)
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    svg = "".join(s.out)
    assert s.M["stable_yards"][-1]["of"] == [600.0, 620.0]  # recorded despite the blocked yard
    assert not s.M["stable_yards"][-1]["rails"] and "#8FA6B0" not in svg  # no rails seated, no water trough drew


def test_stable_yard_rails_avoid_a_neighboring_yards_heap():
    # round 2 (GM 2026-07-25): a later yard must not lay a rail into an earlier yard's muck
    # pile. The baseline _city() stables yard seats its first interior rail at (582.4, 646.7)
    # (seeded RNG); a prior yard's heap planted exactly there forces the candidate through the
    # _rail_clear_of_heaps rejection, and every rail that does draw keeps the 25px hold
    s = _city()
    s.M["stable_yards"] = [{"x": 460, "y": 620, "r": 72.0, "of": [460, 620], "troughs": 0, "rails": [], "dung_heaps": [{"x": 582.4, "y": 646.7, "rx": 2.5, "ry": 1.8}]}]
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    for r in yd["rails"]:
        h = r["len"] / 2
        d = seg_dist(582.4, 646.7, (r["x"] - r["tx"] * h, r["y"] - r["ty"] * h), (r["x"] + r["tx"] * h, r["y"] + r["ty"] * h))
        assert d >= 24.9, f"rail at ({r['x']}, {r['y']}) laid {d:.1f}px from the neighboring yard's heap"


def test_stable_yard_heaps_avoid_a_neighboring_yards_rails():
    # round 2 (GM 2026-07-25): heap clearance is map-wide, not same-yard-only (the Nagahara
    # 22.5px cross-yard defect). The baseline yard drops its first heap at (656.0, 618.6); a
    # prior yard's rail planted there pushes this yard's heaps to spots >= 25px from it
    s = _city()
    fake_rail = {"x": 656.0, "y": 618.6, "tx": 1.0, "ty": 0.0, "len": 18.0, "reach": 2.4}
    s.M["stable_yards"] = [{"x": 740, "y": 620, "r": 72.0, "of": [740, 620], "troughs": 0, "rails": [fake_rail], "dung_heaps": []}]
    s.stables(600, 620, rot=90)
    s.flush_stable_yards()
    yd = s.M["stable_yards"][-1]
    assert yd["dung_heaps"], "the yard should still find room for its muck pile"
    h = fake_rail["len"] / 2
    for dh in yd["dung_heaps"]:
        d = seg_dist(dh["x"], dh["y"], (fake_rail["x"] - h, fake_rail["y"]), (fake_rail["x"] + h, fake_rail["y"]))
        assert d >= 24.9, f"heap at ({dh['x']}, {dh['y']}) sits {d:.1f}px from the neighboring yard's rail"


def test_merchant_residences_stop_at_the_requested_count():
    # the placed >= count early-break: with more storefronts than requested homes, the loop
    # must stop at the cap (previously covered by the towns' legacy gens)
    s = Settlement(W=1600, H=1600, seed=4)
    s.meta(name="Mr", scale="town", ftpx=1)
    rd = [(300, 1100), (1300, 1100)]
    s.road(rd, label="post road")  # merchant_residences derives its band from the ROAD, not a street
    s.frontage(rd, ["shop"] * 8, width=24, spacing=64, skip=rd)
    n0 = sum(1 for b in s.M["buildings"] if b["kind"] == "merchant_large")
    s.merchant_residences(0)  # count already satisfied -> the cap break fires on the first storefront
    assert sum(1 for b in s.M["buildings"] if b["kind"] == "merchant_large") == n0
    s.merchant_residences(1)
    assert sum(1 for b in s.M["buildings"] if b["kind"] == "merchant_large") <= n0 + 1


# ---- the justice works (feature 015) ----------------------------------------------------------
def test_punishment_spot_records_true_size_and_reserves_ground():
    s = _town()
    s.punishment_spot(400, 400, rot=30)
    p = s.M["punishment_spots"][0]
    assert (p["w"], p["h"]) == (30.0, 12.0)  # ~30x12 real ft, true size at town grain (1 ft/px)
    assert p["rot"] == 30.0
    assert (400, 400, 30.0, 12.0) in s.placed  # reserved against the urban pack
    assert s.block_polys  # and against footprint-blocking placers


def test_punishment_spot_draws_no_notice_board():
    # The crime text rides on the cangue, exactly as the historical inscription did - the
    # settlement kosatsuba is a SEPARATE institution and must not be duplicated here.
    s = _town()
    s.punishment_spot(400, 400)
    assert not s.M["kosatsuba"]


def test_execution_ground_label_can_flip_above_the_ground():
    # The ground shares the outskirts with the polluting trades, whose small glyphs the default
    # below-label can land on (Nagahara's kiln works).
    s = _town()
    s.execution_ground(500, 500, label_above=True)
    lb = [line for line in s.M["labels"] if len(line) > 5 and line[5] == "execution ground"][0]
    assert (lb[1] + lb[3]) / 2 < 500


def test_execution_ground_screening_can_be_forced():
    s = _town()
    s.execution_ground(500, 500, screened=True)
    assert s.M["execution_grounds"][0]["screened"] is True
    assert 'stroke-width="1.6"' in "".join(s.out)  # the hoarding on three sides


def test_execution_ground_reads_disused_at_county_tier():
    # ~1 execution per county per 5-10 years: the unscreened ground carries weeds and EMPTY post
    # sockets, never standing posts. A busy scaffold would assert something false about Rokugan.
    s = _town()
    s.execution_ground(500, 500)
    svg = "".join(s.out)
    assert svg.count('stroke="#8A9464"') == 5  # the weed ticks
    assert svg.count('fill="#3A352C"') == 2  # two empty crucifixion mortises


def test_execution_ground_keeps_its_well_out_of_the_household_accounting():
    # The ground's well washes the blade; it serves no household and must never enter the
    # well-density checks.
    s = _town()
    s.execution_ground(500, 500)
    assert not s.M["wells"]


def test_boundary_marker_is_a_location_marker():
    s = _town()
    s.boundary_marker(300, 300)
    b = s.M["boundary_markers"][0]
    assert (b["w"], b["h"]) == (3.0, 3.0)  # TRUE footprint: a real stone is ~3 ft
    assert b["vw"] == b["vh"] == settlement.BOUNDARY_MARKER_MIN_PX  # DRAWN at the legibility floor
    assert (300, 300, b["vw"], b["vh"]) in s.placed  # overlap uses the drawn box, like the wells


def test_boundary_marker_floor_never_shrinks_a_stone():
    # The marker floor lifts a sub-glyph stone; it must not shrink one that already draws larger.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="B", scale="town", ftpx=0.25)  # 4 px per foot - the true stone is already 12 px
    s.boundary_marker(300, 300)
    b = s.M["boundary_markers"][0]
    assert b["vw"] == b["w"] == 12.0


def test_justice_works_can_be_unlabeled():
    s = _town()
    s.punishment_spot(200, 200, label=None)
    s.execution_ground(500, 500, label=None)
    s.boundary_marker(700, 700, label=None)
    assert not s.M["labels"]


def test_punishment_and_execution_captions_tilt_and_keep_their_escapes():
    s = _town()
    s.punishment_spot(500, 500, rot=150)  # the tilted default seat
    assert s.M["labels"][-1][7] == -30.0
    s2 = _town()
    s2.punishment_spot(500, 500, rot=150, label_xy=(430, 470))  # a hand seat keeps its spot, tilted
    L2 = s2.M["labels"][-1]
    assert L2[7] == -30.0 and (L2[0] + L2[2]) / 2 == pytest.approx(430)
    s3 = _town()
    s3.execution_ground(500, 500, rot=164, label_above=True)
    assert s3.M["labels"][-1][7] == -16.0


def test_granary_rot_turns_the_row_and_records_rotated_stores():
    """A riverside complex stands parallel to the bank it loads from (GM 2026-08-09) - the row
    turns as a unit and every store records the rotation, so the matrix tests real corners."""
    s = _cap020()
    s.granary(700, 700, n=3, w=20, h=12, gap=8, label="domain granaries", append=True, rot=-54)
    recs = s.M["granaries"]
    assert len(recs) == 3 and all(r["rot"] == -54 for r in recs)
    assert recs[0]["x"] != recs[1]["x"] and recs[0]["y"] != recs[1]["y"]  # the row marches along the turned axis


def test_granary_append_records_a_list_for_a_capital_with_two_granaries():
    """A capital holds its grain in TWO places for two reasons (the domain's working rice at the
    wharf, the Emperor's stores beside it) - the legacy single M['granary'] dict cannot carry
    both, so append=True records each store into the M['granaries'] LIST instead."""
    s = _cap020()
    s.granary(400, 400, n=3, w=20, h=12, gap=8, label="domain granary", append=True)
    s.granary(800, 300, n=2, w=20, h=12, gap=8, label="Imperial granaries", append=True)
    assert "granary" not in s.M  # the legacy dict is untouched
    assert len(s.M["granaries"]) == 5  # one record per store, so the matrix can see each
    assert {r["label"] for r in s.M["granaries"]} == {"domain granary", "Imperial granaries"}
    assert all("w" in r and "h" in r for r in s.M["granaries"])


# ---- feature 021: districts + retainer terraces -----------------------------------------------


def test_district_records_a_named_region():
    """s.district is a declarative overlay like quarter(): records only, draws nothing (T003)."""
    s = _crop_settlement()
    s.district("east machi", "machi", [(100, 100), (400, 100), (400, 400), (100, 400)])
    s.district("castle foot", "terrace", [(500, 100), (700, 100), (700, 300), (500, 300)], rank_band="terrace")
    d = s.M["districts"]
    assert [r["name"] for r in d] == ["east machi", "castle foot"]
    assert "rank_band" not in d[0] and d[1]["rank_band"] == "terrace"


def test_terrace_draws_one_roof_with_party_wall_seams():
    """The kumi-yashiki range (research 021 item 2): units x 18 ft frontage, 21 ft deep, one
    record for the whole roof, party-wall seams BETWEEN cells (units-1 of them)."""
    s = _crop_settlement()
    s.terrace(500, 500, units=6)
    r = s.M["terraces"][0]
    assert r["units"] == 6 and abs(r["w"] - 6 * 18.0) < 0.1 and abs(r["h"] - 21.0) < 0.1
    assert s.top[-1].count("<line") == 5  # 5 party walls divide 6 cells
    assert any(abs(p[0] - 500) < 0.1 and abs(p[2] - r["w"]) < 0.1 for p in s.placed)


def test_precinct_interior_draws_both_rear_orientations_and_the_graveyard_claim():
    """The sovereign precinct's interior program (020/021): residence, kitchen, dormitories,
    library inside the reserved ground; rear='south' flips the offsets; graveyard=True records
    the claim the cemetery check closes."""
    for rear in ("north", "south"):
        s = Settlement(1000, 1000, seed=11)
        s.precinct_interior(500, 500, rear=rear, graveyard=(rear == "north"))
        p = s.M["precincts"][-1]
        assert p["rear"] == rear
        kinds = [h["kind"] for h in s.M.get("precinct_halls", []) if h.get("precinct") == [500, 500]]
        assert kinds.count("dormitory") >= 2 and "residence" in kinds and "library" in kinds
