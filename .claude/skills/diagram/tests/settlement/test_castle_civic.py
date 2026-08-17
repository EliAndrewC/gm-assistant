"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import os
import tempfile

import pytest

from l7r.diagram import settlement
from l7r.diagram.settlement import Settlement
from tests.settlement._builders import _cap020, _castle_map, _crop_settlement, _ladder_map, _town


def test_forest_patch_uses_default_label_position():
    s = _town()
    s.forest_patch([(100, 100), (300, 120), (320, 300), (110, 280)], label="copse")  # no label_xy -> default
    assert s.M["forest_patches"]


def test_wall_with_a_label():
    s = _town()
    s.wall([(100, 100), (200, 300), (150, 500)], label="rampart")
    assert s.M["wall"]


def test_flower_field_from_a_polygon_base():
    s = _town()
    s.flower_field([(100, 100), (300, 120), (320, 300), (110, 280)], "chrysanthemums", amp=10)
    assert s.M["flower_fields"]


def test_label_hits_counts_a_grove_under_the_label():
    # the _label_hits grove_rects arm: a label box centered on a homestead grove counts it as an
    # obstacle (a label should not sit over a grove canopy).
    s = _crop_settlement()
    s.grove_rects = [(500, 500, 40, 40)]
    assert s._label_hits(500, 500, "Ministry of Test", 12) >= 1


def test_label_hits_counts_gate_furniture_arches_and_wellheads():
    # the ladder's scorer must see every drawn glyph a caption can bury. A torii is a bare [x, y, z]
    # triple and a wellhead has no w/h, so neither is in self.placed and both were invisible to it
    # (GM 2026-07-27) - which is how Tango's theater-stage caption walked onto Benten's gate and its
    # cremation-ground caption onto a well.
    s = Settlement(600, 600, seed=1)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    assert s._label_hits(300, 300, "caption", 11) == 0
    s.M.setdefault("gate_structs", []).append({"x": 300, "y": 300, "w": 20, "h": 12})
    s.M["torii"].append([300, 300, 1])
    s.M["wells"].append({"x": 300, "y": 300, "r": 8, "vr": 4})
    assert s._label_hits(300, 300, "caption", 11) == 3


def test_dojos_roll_follows_the_samurai_cohort():
    # GM formula 2026-07-25: 1 private dojo per full 200 SAMURAI (the city's ~10% share of its
    # population) + a remainder-fraction chance of one extra, floored at 1; count= pins; too few
    # seats is loud. The samurai cohort is the driver, not the population - a dojo serves samurai
    # and nobody else - so the constants are read off the class rather than assumed here.
    def city_(seed, pop):
        s_ = Settlement(1200, 1200, seed=seed)
        s_.meta(name="C", scale="city", ftpx=3)
        s_.M["meta"]["population"] = pop
        return s_

    assert Settlement.DOJO_SAMURAI_FRAC == 0.10 and Settlement.DOJO_PER_SAMURAI == 200
    s = city_(2, 2000)  # 200 samurai = one full unit, zero remainder: exactly 1, no roll can add
    assert s.dojos([(300, 300), (600, 600)]) == 1
    assert s.M["meta"]["dojo_roll"] == 1 and len(s.M["dojos"]) == 1
    s2 = city_(2, 4000)  # 400 samurai = two full units, zero remainder: exactly 2
    assert s2.dojos([(300, 300), (600, 600)]) == 2
    assert len(s2.M["dojos"]) == 2
    # 3,000 -> 300 samurai -> 1 guaranteed + a 50% roll; the two seeds below straddle it
    rolls = {seed: city_(seed, 3000).dojos([(300, 300), (600, 600)]) for seed in (47, 162)}
    assert set(rolls.values()) <= {1, 2}
    assert city_(47, 3000).dojos([(300, 300), (600, 600)], count=2) == 2  # a pin overrides the roll
    s4 = city_(2, 4000)
    with pytest.raises(ValueError, match="vetted seats"):
        s4.dojos([(300, 300)])  # a guaranteed 2 needs 2 seats


def test_martial_hall_and_dojo_draw_their_researched_program():
    # sizes are TRUE feet, not legibility choices (settlements.md "Historical grounding: martial
    # training in a provincial city"): the state hall is a 130x100 ft compound whose archery lane
    # covers the kyudo standard 92 ft shot, a private dojo a 76x44 ft lot with no lane at all.
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="C", scale="city", ftpx=3)
    s.martial_hall(400, 400)
    s.dojo(800, 800)
    (mh,) = s.M["martial_halls"]
    assert (round(mh["w"] * 3), round(mh["h"] * 3)) == (130, 100)
    assert mh["range_ft"] >= 90  # city_martial_hall_has_archery_range's floor
    assert mh["label"] == "martial hall"
    (dj,) = s.M["dojos"]
    assert (round(dj["w"] * 3), round(dj["h"] * 3)) == (76, 44)
    assert "range_ft" not in dj  # no archery lane on a 76 ft lot - the butt is the state hall's
    # the state hall is drawn in government violet, the private hall in ordinary building tan
    assert "#CDBBD6" in s.out[-2] and "#D9C8A4" in s.out[-1]


def test_label_ladder_seats_a_caption_at_the_minimum_standoff_when_the_ground_is_clear():
    s = _ladder_map()
    box = (400.0, 400.0, 500.0, 440.0)  # wider than tall -> below/above are the primary seats
    lx, ly = s._best_label_spot(box, "market", 10)
    assert settlement.box_gap(s._label_box(lx, ly, "market", 10), box) == pytest.approx(settlement.LABEL_MIN_AIR)


def test_label_ladder_steps_outward_past_an_obstacle_and_stops_at_the_first_clear_rung():
    s = _ladder_map()
    box = (400.0, 400.0, 500.0, 440.0)
    clear = s._best_label_spot(box, "market", 10)
    assert settlement.box_gap(s._label_box(*clear, "market", 10), box) == pytest.approx(settlement.LABEL_MIN_AIR)
    for cy in range(370, 476, 7):  # ring the subject so the first rungs are blocked on every side
        for cx in range(330, 576, 12):
            if not (395 < cx < 505 and 395 < cy < 445):
                s.building(cx, cy, 10, 6)
    lx, ly = s._best_label_spot(box, "market", 10)
    gap = settlement.box_gap(s._label_box(lx, ly, "market", 10), box)
    assert gap > settlement.LABEL_MIN_AIR  # the near rungs were blocked...
    assert s._label_hits(lx, ly, "market", 10, pad=0.0, linepad=0.0) == 0  # ...and it kept climbing to clear ground


def test_label_ladder_slides_along_the_long_axis_only():
    # A subject much taller than wide (a road segment, a stall row) is captioned BESIDE it. Sliding
    # ACROSS such a box walks the caption diagonally away while its nominal standoff still reads as
    # small - the first cut of this put "Imperial Road" 43px out at a nominal 5px of air.
    s = _ladder_map()
    tall = (500.0, 200.0, 510.0, 800.0)
    for sl in (-200.0, 200.0):
        seat = s._best_label_spot(tall, "road", 12, slides=(sl,))
        # a slide runs ALONG the subject, so the seat stays tight against it however far it slides;
        # an across-axis slide walked the caption out to 43px at a nominal 5px of air
        assert settlement.box_gap(s._label_box(*seat, "road", 12), tall) <= settlement.LABEL_AIR_CAP * 12


def test_label_ladder_refuses_a_seat_outside_the_cropped_view():
    # a clipped label is unreadable (labels_within_image), so out-of-frame candidates are DISCARDED
    s = _ladder_map()
    box = (100.0, 100.0, 200.0, 140.0)
    free = s._best_label_spot(box, "market", 10)
    assert free[1] > box[3]  # unconstrained, a wide subject is captioned BELOW
    s.M["meta"]["view"] = [60, 60, 400, 90]  # ...but the frame now ends just under the subject
    framed = s._best_label_spot(box, "market", 10)
    assert framed[1] < box[1]  # so the caption moves ABOVE rather than out of the picture


def test_label_ladder_falls_back_to_the_least_covered_seat_when_nothing_is_clear():
    s = _ladder_map()
    box = (400.0, 400.0, 500.0, 440.0)
    for cy in range(320, 540, 10):  # blanket every rung on every side
        for cx in range(300, 620, 10):
            s.building(cx, cy, 14, 8)
    lx, ly = s._best_label_spot(box, "market", 10)
    assert s._label_hits(lx, ly, "market", 10, pad=0.0, linepad=0.0) > 0


def test_place_caption_defers_to_finish_and_records_its_subject_box_for_the_gate():
    # DEFERRED on purpose: a caption seated at call time is judged against half a map (see
    # place_caption's note - Tango's north market caption landed on an execution ground that did
    # not exist yet). Nothing is in M["labels"] until finish() flushes them.
    s = _ladder_map()
    box = (400.0, 400.0, 500.0, 440.0)
    s.place_caption("market", box, 10)
    s.place_caption("ferry", (700.0, 200.0, 720.0, 600.0), 10, slides=(0.0, 40.0))  # explicit slides
    assert not [L for L in s.M["labels"] if L[5] in ("market", "ferry")]
    with tempfile.TemporaryDirectory() as d:
        s.finish(os.path.join(d, "t"), render=False)
    rec = next(L for L in s.M["labels"] if L[5] == "market")
    assert rec[6] == [400.0, 400.0, 500.0, 440.0]
    assert any(L[5] == "ferry" for L in s.M["labels"])


def test_place_caption_refuses_an_empty_subject():
    # s.frontage_box is None when the row placed nothing - captioning it is a gen-script bug
    s = _ladder_map()
    with pytest.raises(ValueError, match="no subject box"):
        s.place_caption("market", None, 10)


def test_label_hits_measures_a_rotated_neighbor_the_way_the_gate_does():
    # `labels_clear_of_other_buildings` boxes a victim by its ROTATED corners' AABB, which is wider
    # than the record's axis-aligned w/h. The probe has to agree, or it waves through exactly what
    # the gate then catches - which is what put Ubame's "caravan inn" in a rot=-16 stables' corner
    # slack the moment the caption's own reach became honest.
    s = _town()
    s.building(300, 300, 92, 44, "stables", rot=-16)
    assert s._label_hits(300, 344, "caravan inn", 9, pad=0.0, linepad=0.0) == 0  # clear of the axis-aligned 92x44...
    assert s._label_hits(300, 344, "caravan inn", 9, pad=0.0, linepad=0.0, tilt=-16) >= 1  # ...inside the rotated AABB the gate reads


def test_place_caption_rot_threads_through_finish(tmp_path):
    s = _town()
    s.place_caption("caravan inn", (100, 100, 180, 160), rot=-16)
    s.finish(str(tmp_path / "t"), render=False)
    L = next(x for x in s.M["labels"] if x[5] == "caravan inn")
    assert len(L) == 8 and L[7] == -16.0 and L[6] == [100.0, 100.0, 180.0, 160.0]


def test_a_castle_caption_can_be_hand_seated():
    """label_xy moves the caption off the court's center - the same escape s.martial_hall keeps."""
    s_def, _ = _castle_map(label="Keep")
    s_hand, _ = _castle_map(label="Keep", label_xy=(1150, 1050))
    assert s_def.M["labels"][-1] != s_hand.M["labels"][-1]


def test_ministry_label_inside_stacks_two_lines_on_the_glyph():
    """The capital's ministry captions sit ON the glyph (GM 2026-08-09) - the estate rule
    applied to the state offices, two stacked lines because the long names cannot fit the
    width in one; a provincial city keeps its beside-captions (smaller compounds)."""
    s = _cap020()
    s.ministry(700, 700, "Ministry of Retainers", label_inside=True)
    recs = [L for L in s.M["labels"] if len(L) > 5 and L[5] in ("Ministry of", "Retainers")]
    assert len(recs) == 2
    for box2 in recs:
        assert box2[0] > 662 and box2[2] < 738 and box2[1] > 675 and box2[3] < 725  # on the glyph
    s2 = _cap020()
    s2.ministry(700, 700, "Records Hall", label_inside=True)  # a non-"Ministry of" office keeps one line
    assert any(len(L) > 5 and L[5] == "Records Hall" for L in s2.M["labels"])


def test_hanko_records_into_the_martial_halls_family():
    """The domain school is the hanko - a school of letters WITH the martial wing - so it draws
    with the martial-hall vocabulary and records into the same family the checks read."""
    s = _cap020()
    s.hanko(700, 700)
    mh = s.M["martial_halls"][0]
    assert mh["kind"] == "hanko" and mh["label"] == "Domain School"
    assert mh["w"] == 133.3 and mh["h"] == 86.7  # 400 x 260 ft (~1 ha) at 3 ft/px - mid-band vs Meirinkan/Nisshinkan
    assert "range_ft" not in mh  # the court is BLANK (sync doctrine) - a dense real hanko belongs to its Mode A sheet
    caption = [L for L in s.M["labels"] if len(L) > 5 and L[5] in ("Domain", "School")]
    assert len(caption) == 2  # the two-line caption sits inside the court, like an estate's
    s2 = _cap020()
    s2.hanko(700, 700, label="Hanko")  # a one-word name keeps the single line
    assert any(len(L) > 5 and L[5] == "Hanko" for L in s2.M["labels"])
