"""Split from test_settlement.py by feature 025 - see test_settlement/CLAUDE.md for the index."""

import math

import pytest

import settlement
from settlement import Settlement
from tests.settlement._builders import _cap020, _city, _crop_settlement, _estate_settlement, _scatter_base_points, _town, _ward_city_with_samurai


def test_clear_label_seat_walks_out_and_gives_up_when_nothing_is_clear():
    # a verge-hugging feature puts its DEFAULT below-label on the frontage it hugs, so the seat is
    # probed: below, above, then left/right, walking outward. On a frontage packed solid there is
    # no clear box at all, and the siter must be told so rather than handed a seat on a shopfront.
    s = _town()
    assert s.clear_label_seat(500, 500, 30, 12, "notice board") == (500, 517)  # the default below-seat, when it is clear
    s.M["buildings"] = [{"x": 500, "y": 500, "w": 2000, "h": 2000, "rot": 0, "kind": "merchant"}]
    assert s.clear_label_seat(500, 500, 30, 12, "notice board") is None
    assert not s.label_seat_clear(500, 517, 26.0)


def test_face_street_rot_without_streets_and_with_a_road():
    s = _town()
    r, d = s._face_street_rot(500, 500)  # no streets at all
    assert r is None and d > 1e17
    s.M["road"] = [[100, 500], [900, 500]]  # the road branch
    r, d = s._face_street_rot(500, 480)
    assert r is not None and d < 100


def test_pack_shortfall_is_reported(capsys):
    # the "no silent caps" principle applied to placement (2026-07-24 town audit: Hirameki's
    # gate market authored 12 businesses, landed 4, and nothing said so)
    s = _town()
    s.pack((100, 100, 130, 130), ["merchant"] * 3)  # room for at most one grid spot
    out = capsys.readouterr().out
    assert "PACK SHORTFALL" in out and "merchant" in out


def test_pack_full_placement_stays_silent(capsys):
    s = _town()
    s.pack((100, 100, 900, 900), ["merchant"] * 2)
    assert "SHORTFALL" not in capsys.readouterr().out


def test_pack_face_streets_true_skips_streetless_ground(capsys):
    # face_streets=True means businesses line a frontage ONLY: with no street within reach,
    # every grid spot is skipped and nothing places (the branch Hirameki's gate-market pack
    # exercised until 2026-07-24, when the market moved to fixed coordinates)
    s = _town()
    n = s.pack((100, 100, 400, 400), ["shop"] * 2, face_streets=True)
    assert n == 0 and "PACK SHORTFALL" in capsys.readouterr().out


def test_kosatsuba_records_a_blocking_struct():
    # the notice board records its manifest entry at true size (~12x5 ft) and reserves its
    # verge (a later pack must not bury the board)
    s = _town()
    z = s.kosatsuba(500, 500, rot=15)
    kb = s.M["kosatsuba"][0]
    assert (kb["x"], kb["y"], kb["w"], kb["h"], kb["rot"]) == (500, 500, 12, 5, 15) and z > 0
    assert (kb["vw"], kb["vh"]) == (12, 5)  # at 1 ft/px the true frame already clears the marker floor
    assert not s._fits(500, 500, 20, 20)
    assert s.M["labels"][-1][1] > 500  # default label sits BELOW the board
    s.kosatsuba(800, 500, label_above=True)  # gate-adjacent boards label ABOVE (clear of the gate)
    assert s.M["labels"][-1][1] < 500


def test_place_kosatsuba_reads_road_and_lane_routes_and_skips_degenerate_segments():
    # the placer reads the SAME manifest route fields as the validator (road + lane + lanes);
    # a zero-length segment (duplicate consecutive points) is skipped, not divided by
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="hamlet", ftpx=1)
    s.M["road"] = [[100, 300], [100, 300], [900, 300]]
    s.M["lane"] = [[100, 700], [900, 700]]
    assert s.place_kosatsuba() is not None
    assert len(s.M["kosatsuba"]) == 1


def test_place_kosatsuba_samples_only_the_main_way_when_one_is_declared():
    # GM 2026-08-02 (Ubame): the board goes ALONG the main road, never a side street - even
    # when the side lane's node is busier. With a road on the map, the lane's verges are not
    # candidates at all, so the board lands in the road's siting band despite every house
    # standing by the lane.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="town", ftpx=1)
    s.M["road"] = [[100, 300], [900, 300]]
    s.M["lane"] = [[100, 700], [900, 700]]
    for i in range(6):
        s.M["houses"].append({"x": 300.0 + 60 * i, "y": 760.0, "w": 30, "h": 20, "kind": "plain", "rot": 0})
        s.placed.append((300.0 + 60 * i, 760.0, 30, 20))
    assert s.place_kosatsuba() is not None
    assert abs(s.M["kosatsuba"][0]["y"] - 300) <= 60  # the road's band, not the busy lane's


def test_kosatsuba_label_xy_hand_seats_the_caption():
    # both caption bands can be taken at a junction seat (Nagahara's market bend: drum tower
    # in the below band, the ward gate's glyph + caption stack in the above band) - label_xy
    # is the explicit hand seat, the same escape the punishment ground carries
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="T", scale="town", ftpx=1)
    s.kosatsuba(500, 500, rot=0, label_xy=(560, 488))
    lab = s.M["labels"][-1]
    assert lab[5] == "notice board"
    assert abs((lab[0] + lab[2]) / 2 - 560) < 2  # seated at the hand x, not the default below-seat


def test_fill_declares_a_capacity_budget_and_stays_silent(capsys):
    # fill=True marks the request as "place up to N" (the city district-fill idiom), so an
    # under-fill is intended, not drift - no warning
    s = _town()
    s.pack((100, 100, 130, 130), ["merchant"] * 3, fill=True)
    s.frontage([(100, 500), (160, 500)], ["merchant"] * 8, fill=True)
    assert "SHORTFALL" not in capsys.readouterr().out


def test_merchant_storehouses_attaches_behind_shops_and_skips_corridors():
    # a kura is tucked behind a merchant's shopfront (its back, opposite the awning) unless that
    # back would land on a street - then it is skipped. rot=0 -> awning faces +y, back faces -y.
    s = _town()
    s.street([(100, 470), (900, 470)], width=24)  # sits just behind shop A's back -> A skipped
    s.building(500, 500, 40, 28, "merchant", rot=0)  # back (-y) runs into the street corridor
    s.building(300, 800, 40, 28, "merchant", rot=0)  # back faces open ground -> kura attached
    n = s.merchant_storehouses(count=6)
    assert n == 1 and len(s.M["storehouses"]) == 1


# ---- the URBAN-CLEARANCE HALO (GM 2026-07-21, Hoshizora): ground-cover stays out of the swept /
# trodden ground AROUND every structure and wellhead, not merely off their footprints - the old
# footprint-only skip scattered scrub through the streets, dooryards, and district gaps of the
# Hoshizora town core. Doctrine + constants: settlement._urban_keepouts. role="pasture" in these
# tests keeps the scatter to tufts + dots (no multi-segment pines), so every element is base-tested.


def test_commons_clears_the_urban_halo_around_buildings():
    s = _crop_settlement()
    s.building(300, 300, 40, 28, "merchant")  # axis-aligned
    s.building(430, 300, 40, 28, "laborer", rot=30)  # rotated - covered by its half-diagonal square
    s.building(1900, 1400, 40, 28, "shop")  # far outside the cover poly - the bbox prefilter drops it
    before = len(s.out)
    s.commons([(150, 150), (600, 150), (600, 500), (150, 500)], role="pasture")
    pts = _scatter_base_points(s.out[before:])
    assert pts  # the open ground beyond the halos still got its scatter
    halo = 30 * s.bscale - 0.06  # the SVG rounds coords to 0.1, so a base just OUTSIDE the halo can print ON its edge
    hd = math.hypot(20, 14) + halo
    for px, py in pts:
        assert not (280 - halo <= px <= 320 + halo and 286 - halo <= py <= 314 + halo)
        assert not (430 - hd <= px <= 430 + hd and 300 - hd <= py <= 300 + hd)


def test_commons_keeps_scrub_off_the_road_bed():
    # the old skip knew only LANES, so scrub drew on the Imperial Road bed (Hoshizora); the
    # corridor set now covers lanes + town streets + the road
    s = _crop_settlement()
    s.road([(100, 300), (700, 300)])
    before = len(s.out)
    s.commons([(150, 150), (600, 150), (600, 450), (150, 450)], role="pasture")
    lim = s.M["road_width"] / 2 + 3 * s.bscale - 0.06  # 0.1-rounding slack, as in the halo test
    pts = _scatter_base_points(s.out[before:])
    assert pts and all(abs(py - 300) > lim for px, py in pts if 100 <= px <= 700)


def test_marsh_clears_the_urban_halo_and_wellheads():
    s = _crop_settlement()
    s.building(300, 300, 40, 28, "merchant")
    s.well(460, 300)
    before = len(s.out)
    s.marsh([(150, 150), (600, 150), (600, 450), (150, 450)])
    lim = s.M["wells"][0]["vr"] + 20 * s.bscale - 0.06  # 0.1-rounding slack, as in the halo test
    halo = 30 * s.bscale - 0.06
    pts = _scatter_base_points(s.out[before:])
    assert pts
    for px, py in pts:
        assert not (280 - halo <= px <= 320 + halo and 286 - halo <= py <= 314 + halo)
        assert (px - 460) ** 2 + (py - 300) ** 2 > lim * lim


def test_place_punishment_spot_probes_for_a_clear_caption_seat():
    """The display board's caption gets its own probe, because a verge-hugging feature's default
    below-label lands on the frontage it hugs - which is what 'hugging the frontage' means."""
    s = _crop_settlement()
    s.street([(200, 300), (800, 300)], width=10)
    # a shopfront row along the south verge, so the caption's DEFAULT seat below the board is taken
    # and the probe has to walk outward to a clear one
    for _bx in range(210, 800, 30):
        s.building(_bx, 322, 26, 16, "shop")
    # ...and existing CAPTIONS strung along the verge bands, so the probe also has to reject seats
    # that are clear of every building but would bury another label
    for _ly in range(240, 390, 9):
        for _lx in range(210, 820, 55):
            s.label(_lx, _ly, "riverside quarter", 9)
    spot = s.place_punishment_spot()
    assert spot is not None and s.M["punishment_spots"]
    cap = next(lb for lb in s.M["labels"] if len(lb) > 5 and lb[5] == "punishment ground")
    # the real property: wherever the probe put it, the caption sits on NO shopfront
    for b in s.M["buildings"]:
        bx0, by0 = b["x"] - b["w"] / 2, b["y"] - b["h"] / 2
        bx1, by1 = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
        assert not (cap[0] < bx1 and bx0 < cap[2] and cap[1] < by1 and by0 < cap[3]), f"caption on {b['kind']} at ({b['x']}, {b['y']})"


def test_merchant_residences_places_behind_band_and_skips_bad_spots():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])  # horizontal road
    s.building(850, 640, 40, 28, "shop", rot=180)  # a DEEP, far shop: raises the band depth so the others'
    #                                                       homes land well behind their own shop (clearance)
    s.building(300, 560, 40, 28, "shop", rot=180)  # its home lands ~(300,684), clear -> PLACES
    s.building(395, 560, 40, 28, "shop", rot=180)  # home ~95px away: clears overlap but within `spread` -> skipped
    s.building(600, 560, 40, 28, "shop", rot=180)  # its home ~(600,684) lands in the paddy below -> skipped
    s.paddy_field((540, 650, 660, 760), "", "p", amp=6)  # a paddy under the 600-shop's home (blocked ground)
    n = s.merchant_residences(count=6)
    homes = [b for b in s.M["buildings"] if b["kind"] == "merchant_large"]
    assert n >= 1 and homes and all(h["y"] > 600 for h in homes)  # placed BEHIND the band (further from the road)


def test_merchant_residences_skips_an_off_map_home():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])
    s.building(300, 950, 40, 28, "shop", rot=180)  # so deep that its home lands ~y=994, off the bottom edge
    assert s.merchant_residences() == 0


def test_merchant_residences_respects_the_bound():
    s = Settlement(1000, 1000, seed=1)
    s.road([(50, 500), (950, 500)])
    s.building(850, 640, 40, 28, "shop", rot=180)  # deep+far: raises band depth so the 300-home clears its shop
    s.building(300, 560, 40, 28, "shop", rot=180)  # its home lands ~(300,684), clear of shops
    s.bound = [(0, 0), (1000, 0), (1000, 600), (0, 600)]  # bound excludes y > 600 -> the 300-home is outside -> skipped
    assert s.merchant_residences() == 0


def test_rowpack_lays_touching_terraces():
    # the GM row-packing doctrine: city commoner housing goes down as CONTIGUOUS terraces -
    # most units share a party wall (hairline seam <= 1.2px), never the old detached scatter
    s = _city()
    n = s.rowpack((200, 200, 600, 330), ["laborer"] * 40)
    assert n >= 25
    bs = s.M["buildings"]

    def egap(a, b):
        dx = abs(a["x"] - b["x"]) - (a["w"] + b["w"]) / 2
        dy = abs(a["y"] - b["y"]) - (a["h"] + b["h"]) / 2
        return max(dx, dy)

    gaps = [min(egap(a, b) for j, b in enumerate(bs) if j != i) for i, a in enumerate(bs)]
    assert sum(1 for g in gaps if g <= 1.2) >= 0.55 * len(bs)


def test_rowpack_respects_canvas_edge_and_bound():
    # rows must not spill off the canvas margins (title/edge zone) or outside a bounding
    # ring (the city's ring road) - both rejections clip the terrace, they don't crash it
    s = _city()
    s.rowpack((20, 200, 200, 260), ["laborer"] * 30)  # zone hangs past the x<55 edge margin
    assert all(b["x"] - b["w"] / 2 >= 55 for b in s.M["buildings"])
    s2 = _city()
    s2.bound = [(300, 100), (700, 100), (700, 500), (300, 500)]
    s2.rowpack((200, 200, 600, 300), ["laborer"] * 30)  # zone's west half lies outside the bound
    assert all(b["x"] - b["w"] / 2 >= 299 for b in s2.M["buildings"])


def test_rowpack_blocked_zone_terminates_and_places_nothing():
    # a zone fully covered by an earlier structure yields no houses: every row scans past the
    # obstacle, the row pitch still advances, and the loop ends at the zone's south edge
    s = _city()
    s.building(400, 250, 420, 130, "civic")  # a compound covering the whole zone
    assert s.rowpack((200, 200, 600, 300), ["laborer"] * 30) == 0


def test_pack_businesses_only_line_the_frontage():
    # face_streets=True (businesses mode): a spot with no street within reach places NOTHING -
    # shops exist to catch passing feet, they never scatter into a streetless interior. (This
    # mode lost its last pool caller in the 2026-07-24 Hirameki roadway rework; the unit test
    # keeps the API branch alive and covered.)
    s = Settlement(1000, 1000, seed=2)
    s.meta(name="T", scale="town")
    s.pack((150, 300, 850, 700), ["merchant"] * 6, step=40, face_streets=True)
    assert s.M["buildings"] == []


def test_ministry_auto_label_side_prefers_empty_ground():
    # the GM label doctrine (2026-07): a label that CAN sit in empty ground, should. With no
    # label_below override the ministry scores both spots against what is already placed and
    # takes the clearer; the default (unpassed) size is the real ~224x148 ft compound.
    s = Settlement(1000, 1000, seed=4)
    s.meta(name="C", scale="city", ftpx=3)
    s.building(500, 462, 90, 24, "civic")  # crowd the ABOVE label spot
    s.ministry(500, 510, "Ministry of Test")
    assert s.M["ministries"][0]["w"] == s.px(224)
    lab = next(lb for lb in s.M["labels"] if lb[5] == "Ministry of Test")
    assert (lab[1] + lab[3]) / 2 > 510  # the label went BELOW, into the open ground


def test_estate_wall_must_stand_on_dry_private_ground():
    """The municipal watch cannot be walled inside a private court, and the compound wall may not run
    through working water. Each refusal path asserted directly rather than left to map geometry."""
    s = _estate_settlement()
    assert s._estate_wall_clear(600, 600, 100, 80)  # clear ground
    s.M["fire_towers"] = [{"x": 600, "y": 600, "w": 10, "h": 10}]  # tower swallowed by the court
    assert not s._estate_wall_clear(600, 600, 100, 80)
    s2 = _estate_settlement()
    s2.M["fire_towers"] = [{"x": 650, "y": 600, "w": 10, "h": 10}]  # tower ON the wall line
    assert not s2._estate_wall_clear(600, 600, 100, 80)
    s3 = _estate_settlement()
    s3.M["canals"] = [{"poly": [(650, 400), (650, 800)], "w": 12}]  # canal crossing the wall
    assert not s3._estate_wall_clear(600, 600, 100, 80)
    s4 = _estate_settlement()
    s4.M["pond"] = (650, 600, 40, 40)  # pond under the wall
    assert not s4._estate_wall_clear(600, 600, 100, 80)


def test_merchant_estate_raises_when_no_clear_seat_exists():
    """Rather than draw a wall the gate will reject, an estate boxed in by water raises."""
    s = _estate_settlement()
    s.M["canals"] = [{"poly": [(x, 0), (x, 1200)], "w": 12} for x in range(400, 900, 40)]  # a thicket of canals
    with pytest.raises(ValueError, match="no seat within the slide fan"):
        s.merchant_estate(600, 600, 100, 80)


def test_merchant_estates_rolls_seats_and_records_the_target():
    import random as _rr

    from settlement import roll_merchant_estate_count

    s = Settlement(1200, 1200, seed=11)
    s.meta(name="c", scale="city", ftpx=3)
    expect = roll_merchant_estate_count("city", _rr.Random(11 * 1201 + 89))  # the method's dedicated stream
    n = s.merchant_estates([(300, 300, "south"), (600, 300, "south"), (300, 600, "east")])
    assert n == expect
    assert len(s.M["merchant_estates"]) == n
    assert s.M["meta"]["merchant_estate_roll"] == n


def test_merchant_estates_pin_overrides_the_roll():
    s = Settlement(1200, 1200, seed=11)
    s.meta(name="c", scale="city", ftpx=3)
    n = s.merchant_estates([(300, 300, "south"), (600, 300, "south"), (300, 600, "east")], count=2)
    assert n == 2
    assert len(s.M["merchant_estates"]) == 2
    assert s.M["meta"]["merchant_estate_roll"] == 2


def test_merchant_estates_raises_when_seats_run_short():
    s = Settlement(1200, 1200, seed=11)
    s.meta(name="c", scale="city", ftpx=3)
    with pytest.raises(ValueError, match="vetted seats"):
        s.merchant_estates([(300, 300, "south")], count=3)


def test_place_punishment_spot_is_a_no_op_when_opted_out():
    s = _town()
    s.meta(punishment_spot=False)
    s.road([(100, 500), (900, 500)])
    assert s.place_punishment_spot() is None
    assert not s.M["punishment_spots"]


def test_place_punishment_spot_needs_a_street_to_site_on():
    # No road, no town street, no lane: there is no traffic to site the display on, so the siter
    # declines rather than dropping it somewhere arbitrary (the presence check then fires).
    s = _town()
    assert s.place_punishment_spot() is None


def test_place_punishment_spot_skips_a_degenerate_route_segment():
    s = _town()
    s.M["road"] = [[100, 500], [100, 500], [900, 500]]  # a repeated point: zero-length segment
    assert s.place_punishment_spot() is not None


def test_place_punishment_spot_declines_when_no_verge_is_within_the_siting_band():
    # At a very coarse grain the ~60-real-ft band is narrower than the road's own tread plus the
    # feature, so no candidate offset is legal at all - the siter must return None, not guess.
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="C", scale="city", ftpx=30)
    s.road([(100, 500), (900, 500)])
    assert s.place_punishment_spot() is None


def test_place_punishment_spot_walks_the_label_off_a_building_it_would_cover():
    s = _town()
    s.road([(100, 500), (900, 500)])
    s.building(145, 536, 20, 20, "merchant")  # sits under the DEFAULT below-label, not under the spot
    spot = s.place_punishment_spot()
    assert spot is not None
    lb = [line for line in s.M["labels"] if len(line) > 5 and line[5] == "punishment ground"][0]
    below_default = spot[1] + s.px(12) / 2 + 11
    assert abs((lb[1] + lb[3]) / 2 - below_default) > 4  # the label moved off its default band


def test_martial_hall_caption_takes_the_emptier_side():
    # "martial hall" is wide relative to a 43x33 px compound, so the caption side is a real
    # decision: a hall seated beside the yamen would otherwise drop its label on the governor.
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="C", scale="city", ftpx=3)
    s.building(400, 440, 120, 40, kind="samurai")  # a neighbor directly BELOW the hall's seat
    s.martial_hall(400, 400)
    lab = [L for L in s.M["labels"] if len(L) > 5 and L[5] == "martial hall"][0]
    assert lab[1] < 400  # pushed ABOVE the compound, away from the occupied side


def test_merchant_storehouse_is_never_drawn_across_a_neighbor():
    """A kura's overlap is legitimate only because it is an annex of ITS OWN shop. One tucked behind
    a narrow shopfront that happens to back onto the next lot's larger house is a defect - the case
    the old blanket storehouse exemption could not express, and which the matrix found twice."""
    s = _town()
    s.building(500, 500, 54, 36, "merchant", rot=0)
    s.building(500, 455, 86, 60, "merchant_large", rot=0)  # squarely BEHIND it (rot=0 puts the kura north)
    assert s.merchant_storehouses(count=4) == 0
    s2 = _town()
    s2.building(500, 500, 54, 36, "merchant", rot=0)
    assert s2.merchant_storehouses(count=4) == 1  # nothing behind it - the annex is fine


def test_theater_stage_caption_clears_the_rotated_ground():
    """A caption must be seated against the extent the feature is DRAWN at, not its raw half-height.

    `theater_stage` offset its label by `cy + hh + 16`, the reach along +y only when the stage is
    upright. Ubame's stage stands at rot=90, where the ground reaches `hw` along +y - so the caption
    landed INSIDE the ground it names, the outline stroke running through the text
    (settlement-review, 2026-07-26). No check saw it: `labels_clear_of_other_buildings` polices a
    caption sitting on features it does NOT name, and this one sat on the one it did.

    Correcting the reach alone was not enough - a hand seat knows nothing about its neighbors, and
    the corrected offset dropped Tango's caption onto a monk house. So the caption is now seated by
    the STANDOFF LADDER against the rotated extent, HINTED at the historical spot, which keeps every
    upright stage exactly where it was whenever that seat is clear.

    Asserted on the queued caption rather than M["labels"]: `place_caption` defers seating until
    `finish()`, so the label does not exist yet at this point.
    """
    for rot, box, hint in (
        (90, (458, 340, 542, 460), (500, 476)),  # rotated: reach along +y is hw=60, not hh=42
        (0, (440, 358, 560, 442), (500, 458)),  # upright: cy + hh + 16, the historical seat
    ):
        s = _town()
        s.theater_stage(500, 400, 120, 84, rot=rot, label="theater stage")
        assert len(s._captions) == 1, "the stage caption must be queued for the standoff ladder"
        text, bx, _sz, _it, _wt, _co, hi, _sl, _ro = s._captions[0]
        assert text == "theater stage"
        assert tuple(round(v) for v in bx) == box, f"rot={rot}: caption boxed against the wrong extent"
        assert tuple(round(v) for v in hi) == hint, f"rot={rot}: caption hinted at the wrong seat"
        assert _ro == 0.0, f"rot={rot}: both are square rotations, so the caption stays level"


def test_building_refuses_commoners_inside_a_declared_samurai_ward():
    # GM 2026-08-02 (Minami): whole-interior top-up sweeps seated laborers and a merchant row
    # inside the ward fence. Once s.ward has run, the engine refuses those seats at s.building
    # itself - the one chokepoint every pack, frontage and gen-side top-up funnels through.
    s = Settlement(1000, 1000, seed=1)
    s.M["wall"] = [[200, 200], [800, 200], [800, 800], [200, 800]]
    s.ward("samurai", [(400, 795), (400, 400), (795, 400)], gates=[])
    assert s.building(600, 600, 16, 11, "laborer") is False
    assert all(b["kind"] != "laborer" for b in s.M["buildings"])
    assert s.building(600, 600, 16, 11, "samurai") is True  # a resident seats normally
    assert s.building(250, 250, 16, 11, "laborer") is True  # outside the fence - unaffected


def test_compound_and_marker_captions_tilt_with_their_glyphs():
    s = _town()
    s.manor(500, 300, 120, 90, "Manor", sublabel="the bench", rot=-30)
    recs = {L[5]: L for L in s.M["labels"]}
    assert recs["Manor"][7] == -30.0 and recs["the bench"][7] == -30.0
    s.kosatsuba(200, 700, rot=-29)
    assert s.M["labels"][-1][7] == -29.0
    s.fire_tower(800, 700, rot=150)
    assert s.M["labels"][-1][7] == -30.0
    s.boundary_marker(850, 200, rot=-16)
    assert s.M["labels"][-1][7] == -16.0


def test_label_seat_clear_probes_the_tilted_reach():
    s = _town()
    s.M["houses"].append({"x": 300, "y": 262, "w": 40, "h": 24})
    tw = s.label_caption_hw("a long caption here", 9)
    assert s.label_seat_clear(300, 300, tw, 9)  # the level box clears under the house
    assert not s.label_seat_clear(300, 300, tw, 9, tilt=-30.0)  # the tilted reach swings up into it


def test_servant_ranges_attach_to_their_own_household():
    # GM 2026-08-02: a ward servant is its household's nagaya, drawn along its master's frontage
    s = _ward_city_with_samurai((600, 600, "samurai", 0.0), (600, 700, "samurai_large", 0.0))
    n = s.servant_ranges()
    assert n == 3  # one range for the junior house, two for the senior (budgets.md)
    ranges = [b for b in s.M["buildings"] if b["kind"] == "servant"]
    assert len(ranges) == 3
    for r in ranges:
        assert r["of"] in ([600.0, 600.0], [600.0, 700.0])
        assert r["w"] > 2.2 * r["h"]  # a RANGE, not a cottage - the proportion carries the read
        assert r["h"] == pytest.approx(s.px(s.SERVANT_RANGE_DEPTH_FT))


def test_servant_ranges_is_a_noop_without_a_ward():
    s = Settlement(1000, 1000, seed=1)
    s.meta(name="W", scale="city", ftpx=3)
    s.building(600, 600, *s._dims("samurai"), "samurai", 0.0)
    assert s.servant_ranges() == 0


def test_building_refuses_a_freestanding_servant_inside_the_ward():
    # barring the commoner kinds alone just handed their ground to the servant packs
    s = _ward_city_with_samurai((600, 600, "samurai", 0.0))
    assert s.building(700, 700, 10, 7, "servant") is False
    assert s.building(150, 150, 10, 7, "servant") is True  # outside the fence, unaffected


def test_servant_ranges_is_idempotent():
    # it may be re-run after a late household top-up; nobody gets a second range over quota
    s = _ward_city_with_samurai((600, 600, "samurai", 0.0), (600, 700, "samurai_large", 0.0))
    first = s.servant_ranges()
    assert first == 3
    assert s.servant_ranges() == 0
    assert sum(1 for b in s.M["buildings"] if b["kind"] == "servant") == 3


def test_servant_ranges_skips_a_house_too_narrow_to_carry_a_range():
    # below ~2.3x the range depth it stops reading as a range and starts reading as a cottage,
    # so the household simply gets none - its servants sleep under the master's roof
    s = _ward_city_with_samurai()
    s.building(600, 600, 8, 6, "samurai", 0.0)
    assert s.servant_ranges() == 0


def test_door_is_clear_rejects_a_blocked_doorway():
    s = _ward_city_with_samurai()
    s.building(600, 608, 20, 10, "monk_house", 0.0)  # squarely across the doorway of the seat below
    assert not s._door_is_clear(600, 600, 20, 6, 0.0)
    assert s._door_is_clear(600, 400, 20, 6, 0.0)  # same footprint, open ground ahead


def test_servant_ranges_refuses_a_seat_whose_own_door_is_blocked():
    # the range is a dwelling too: its own entrance has to open onto something
    probe = _ward_city_with_samurai((600, 600, "samurai", 0.0))
    probe.servant_ranges()
    seat = next(b for b in probe.M["buildings"] if b["kind"] == "servant")
    s = _ward_city_with_samurai((600, 600, "samurai", 0.0))
    # 1.2 px clear of the range - further than its 0.6 px gap to its own host, so the nearest-host
    # rule does not refuse it first, yet inside the ~2.3 px band the door check samples
    s.building(seat["x"], seat["y"] + seat["h"] / 2 + 3.2, seat["w"], 4, "monk_house", 0.0)
    s.servant_ranges()
    seated = [(round(b["x"], 1), round(b["y"], 1)) for b in s.M["buildings"] if b["kind"] == "servant"]
    assert (round(seat["x"], 1), round(seat["y"], 1)) not in seated  # that seat is refused; another flank may still serve


def test_manor_label_inside_fits_the_court():
    """A city estate's caption lives INSIDE the blank court (GM 2026-08-09), sized to clear the
    walls - and a small estate gets a smaller face rather than an overflowing one."""
    s = _cap020()
    s.manor(700, 700, 150, 118, "Hazama Estate", label_inside=True)
    lines = [L for L in s.M["labels"] if len(L) > 5 and L[5] in ("Hazama", "Estate")]
    assert len(lines) == 2  # split over two lines so the face runs bigger (GM 2026-08-09)
    for box in lines:
        assert box[0] > 625 and box[2] < 775 and box[1] > 641 and box[3] < 759  # fully inside the court
    s2 = _cap020()
    s2.manor(700, 700, 70, 54, "Lone", label_inside=True)  # a one-word label keeps the single line
    assert any(len(L) > 5 and L[5] == "Lone" for L in s2.M["labels"])


def test_theater_stage_records_every_stage_not_just_the_last():
    """TWO theater stages on one map (a temple stage AND an entertainment-quarter theater -
    Shiro Daika's design) must BOTH reach the manifest. The singleton dict write meant the
    second call clobbered the first: the labeled quarter stage existed as ink only, invisible
    to the overlap matrix in both directions (settlement-review, 2026-08-10)."""
    s = Settlement(1000, 1000, seed=7)
    s.theater_stage(300, 300, w=66, h=48, label=None)
    s.theater_stage(700, 700, w=64, h=46, rot=-120, kind="monzen", label=None)
    recs = s.M["theater_stage"]
    assert isinstance(recs, list) and len(recs) == 2
    assert {(r["x"], r["y"]) for r in recs} == {(300, 300), (700, 700)}
    assert recs[0].get("kind") == "machi" or recs[0].get("kind") == "monzen" or "kind" in recs[0]


def test_a_dense_row_lines_a_way_that_bends_inside_the_fronted_stretch():
    """The fronted stretch and the way's own corridor segments rarely coincide: a road runs the
    height of the map and a shop row lines 500 px of it, and the road BENDS inside that stretch.
    Matching a segment only when the whole stretch lies on it left the way's cleared band refusing
    the shops meant to line it - 325 refusals on the capital's Imperial road. A dense row counts a
    segment as running along the stretch if EITHER contains the other."""
    # a real road is a polyline of SHORT segments with a slight drift, so no one segment contains
    # the whole stretch a shop row lines - which is the case that used to match nothing at all
    road = [(300, 100), (300, 400), (305, 700), (310, 1000)]

    def run(dense):
        s = settlement.Settlement(1000, 1000, seed=11)
        s.meta(scale="city", ftpx=3)
        s.road(road, width=s.lw(30))
        # the row is written as its OWN two-point stretch spanning several road segments, which is
        # how a gen writes a sub-stretch - not the road object the corridor was registered with
        return s.frontage([(300, 150), (308, 950)], ["merchant"] * 24, width=6, spacing=26, setback=2, both=False, dense=dense)

    assert run(True) > run(False), "a dense row must not be refused by the band of the way it lines"
