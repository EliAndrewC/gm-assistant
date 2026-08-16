"""Split from test_settlement.py by feature 025 - see tests/settlement/CLAUDE.md for the index."""

import math

import pytest

import settlement
from settlement import Settlement
from tests.settlement._builders import _byre_village, _caption_size, _crop_settlement, _nuc_village, _scatter_base_points, _town, _village, _walled_city


def test_a_wellhead_is_refused_in_the_paddy_water_and_allowed_on_the_rim():
    # the PLACEMENT half of wells_clear_of_paddies - both halves read paddy_wet_rings, so the siter
    # and the check cannot disagree about where the water is (the same-source doctrine)
    s = _town()
    basin = [[600, 600], [900, 600], [900, 900], [600, 900]]
    s.M["fields"] = [{"name": "f1", "kind": "paddy", "outline": [[400, 400], [900, 400], [900, 900], [400, 900]], "plot_polys": [basin]}]
    assert not s._well_ground_clear(750, 750)  # in the water
    assert not s._well_ground_clear(750, 594)  # the drawn head laps a basin's edge
    assert s._well_ground_clear(450, 450)  # the fan's unplanted rim slack, inside the envelope
    s.M["fields"][0]["plot_polys"] = [[[0, 0], [1, 1]]]  # a field drawing no real basins...
    assert not s._well_ground_clear(450, 450)  # ...falls back to its outline, as the rural tiers do
    s.M["fields"][0]["outline"] = [[0, 0]]  # and one drawing nothing at all contributes no water
    assert s._well_ground_clear(450, 450)
    s.M["fields"][0]["kind"] = "dry"  # a DRY field is not this rule's business
    assert s._well_ground_clear(750, 750)


def test_torii_path_places_one_torii_per_interior_vertex():
    s = _town()
    s.torii_path([(0, 0), (50, 50), (100, 0)])
    assert len(s.M["torii"]) == 1


def test_torii_even_runs():
    s = _town()
    s.torii_even([(0, 0), (100, 0), (100, 100)], 4)
    assert len(s.M["torii"]) == 4


def test_tree_stand_canopy_is_deferred_and_never_drawn_over_a_building_or_well():
    # the canopy is QUEUED at forest_patch() time and drawn at flush, so it is filtered against the
    # COMPLETE map: a building and a well placed AFTER the wood still end up with clear roofs.
    s = _town()
    s.forest_patch([(300, 300), (900, 300), (900, 900), (300, 900)])
    assert not s.M["tree_crowns"]  # nothing drawn yet - only the litter floor is down
    s.building(600, 600, 60, 40, "merchant", 0)
    s.well(500, 500)
    s.flush_tree_stands()
    crowns = s.M["tree_crowns"]
    assert crowns  # the stand itself did draw
    b = s.M["buildings"][-1]
    wl = s.M["wells"][-1]
    for i in range(0, len(crowns), 3):
        x, y, r = crowns[i], crowns[i + 1], crowns[i + 2]
        # CIRCLE vs RECT, the same rounded-corner measure `_crown_covers` and the gate's
        # structures_clear_of_trees use - NOT the naive AABB this line used to carry. The AABB
        # includes the four CORNER squares a circle cannot reach, so it called a crown sitting
        # diagonally off a corner an overlap: (562.5, 573.7) r=8.7 against a 60x40 building at
        # (600, 600) is 7.5 x 6.3 px clear of the nearest corner, i.e. 9.8 px away from a crown
        # that reaches 8.7. It only ever passed because no crown had landed in a corner diagonal
        # before the 2026-08-08 re-roll put one there (test geometry stricter than the rule it
        # guards is a false alarm waiting for a re-roll).
        dx, dy = max(abs(x - b["x"]) - b["w"] / 2, 0.0), max(abs(y - b["y"]) - b["h"] / 2, 0.0)
        assert dx * dx + dy * dy >= r * r
        assert math.hypot(x - wl["x"], y - wl["y"]) >= r + wl.get("vr", wl["r"])
    n = len(crowns)
    s.flush_tree_stands()  # idempotent - the queue is drained
    assert len(s.M["tree_crowns"]) == n


def test_fringe_trees_keep_off_the_crop():
    # the wood's advance-growth fringe seeds on waste ground, never in a worked field
    s = _town()
    s.field_polys.append([(100, 100), (400, 100), (400, 400), (100, 400)])
    assert s._fringe_blocked(250, 250, 8) is True  # inside the crop
    assert s._fringe_blocked(392, 250, 8) is True  # ... and within a crown's reach of its edge
    assert s._fringe_blocked(700, 700, 8) is False  # open waste ground


def test_commons_clears_the_wellhead_apron():
    s = _crop_settlement()
    s.well(300, 300)
    before = len(s.out)
    s.commons([(150, 150), (500, 150), (500, 450), (150, 450)], role="pasture")
    lim = s.M["wells"][0]["vr"] + 20 * s.bscale - 0.06  # 0.1-rounding slack, as in the halo test
    pts = _scatter_base_points(s.out[before:])
    assert pts and all((px - 300) ** 2 + (py - 300) ** 2 > lim * lim for px, py in pts)


def test_commons_keeps_scrub_off_a_shrine_and_torii():
    # a commons that OVERLAPS the shrine must not scatter scrub over the hall or its torii arch (both are
    # block_polys); the skip is per-tuft, so the plot is still recorded
    s = _nuc_village()
    s.shrine_hall(320, 400, "", w=60, h=48, kind="shrine", torii=[(320, 330)], graveyard=False)
    s.commons([(220, 150), (420, 150), (420, 650), (220, 650)])  # straddles the shrine + torii blocks
    assert len(s.M["commons"]) == 1


def test_marsh_keeps_reeds_off_a_building():
    s = _crop_settlement()
    s.shrine_hall(300, 300, "", w=60, h=48, kind="shrine", graveyard=False)  # a block_poly inside the marsh
    s.marsh([(150, 150), (500, 150), (500, 450), (150, 450)])  # reeds on the hall are skipped
    assert len(s.M["marshes"]) == 1


def test_shrine_hall_extends_a_multi_point_avenue_along_its_own_step():
    # >= 2 given points: extension continues the avenue's OWN stride, not the 44px default
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 570)], torii_count=3)
    # a 10px (30 ft) authored stride is inside the pitch band, so it stands - but the whole run is
    # slid in to the hall's threshold (front edge y514 + the 10px stride), which is _avenue_at_threshold's job
    assert sorted(t[1] for t in s.M["torii"]) == pytest.approx([524, 534, 544], abs=0.1)


def test_shrine_hall_roll_below_geometry_draws_the_first_n():
    # a roll/pin smaller than the supplied avenue keeps the arches nearest the hall
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 598), (600, 636)], torii_count=1)
    assert [t[1] for t in s.M["torii"]] == pytest.approx([500 + s.px(84) / 2 + s.px(settlement.TORII_PITCH_FT)], abs=0.1)  # ...seated at the threshold


def test_torii_refuses_a_seat_standing_in_a_wall():
    # a torii is a freestanding gateway; an arch set INTO a barrier is impossible construction, so
    # the primitive refuses it outright (the hand-placed path - an avenue shortens itself instead)
    s = _walled_city()
    with pytest.raises(ValueError, match="would stand in the samurai ward fence"):
        s.torii_path([(600, 600), (600, 700), (600, 800)])


def test_shrine_hall_shortens_its_avenue_short_of_a_wall():
    # the avenue is pulled BACK as a whole (uniform stride) so the rolled count still fits on open
    # ground rather than marching the last arches into the fence. The run is threshold-seated at the
    # hall's front edge (y514) with a 10px (30 ft, inside the pitch band) stride, so 7 arches would
    # reach y584 and cross the fence at y570.
    s = _walled_city(fence=((300, 570), (900, 570)))
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 570)], torii_count=7)
    ys = [t[1] for t in s.M["torii"]]
    assert len(ys) == 7  # every rolled arch is drawn
    assert ys[-1] < 566 and settlement.torii_wall_conflicts(s.M) == []  # shortened to stop before the fence, all clear
    strides = [ys[i + 1] - ys[i] for i in range(6)]
    assert max(strides) - min(strides) <= 0.2  # ... and still evenly spaced (the run is scaled, not re-seated one by one)
    # ...and the THRESHOLD is re-taken after the shortening: pulling the stride in would otherwise
    # leave the innermost arch standing at the old, wider gap from the hall (GM 2026-07-27).
    assert ys[0] - 514 == pytest.approx(strides[0], abs=0.2)


def test_shrine_hall_refuses_an_avenue_that_cannot_be_shortened_clear():
    # if even the first arch stands in the wall, no shortening helps: fail the gen rather than
    # close the arches up on each other or fudge the geometry
    # (the message names "a wall" rather than the fence here: no single arch STANDS in it - it is the
    # walk between them that crosses - so torii_seat_on_wall has no run to name for the first arch)
    s = _walled_city(fence=((300, 545), (900, 545)))
    with pytest.raises(ValueError, match="cannot be shortened clear of a wall"):
        s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 570)], torii_count=7)


def test_shrine_hall_repitches_an_overwide_avenue_along_its_own_line():
    # GM 2026-07-25: the gen authors the avenue's LINE, the engine owns its STRIDE. An authored run
    # wider than two rail-spans is re-laid at the ~20 ft house pitch, resampled by arc length along
    # the authored line - so a CURVED sando keeps its curve and its innermost seat, only tightening.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 560), (600, 598), (640, 636)], torii_count=3)
    ts = s.M["torii"]
    step = s.px(settlement.TORII_PITCH_FT)
    assert ts[0][0] == 600 and ts[0][1] == pytest.approx(500 + s.px(84) / 2 + step, abs=0.1)  # innermost arch one pitch off the hall's front
    gaps = [math.hypot(ts[i + 1][0] - ts[i][0], ts[i + 1][1] - ts[i][1]) for i in range(2)]
    assert gaps == pytest.approx([step, step], abs=0.15)  # evenly re-pitched to the house stride
    assert all(t[0] == 600 for t in ts)  # ... and still on the authored line's first leg (it never reaches the bend)


def test_shrine_hall_leaves_an_avenue_inside_the_pitch_band_alone():
    # the village avenues (~30 ft, 1.9 rail-spans) are deliberate and must not be re-pitched: within
    # the band the gen's own spacing stands, so only the over-wide town/city runs are touched
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="V", scale="village", ftpx=2, down_deg=90)
    s.shrine_hall(600, 500, "Shrine", w=s.px(60), h=s.px(48), torii=[(600, 560), (600, 575), (600, 590)], torii_count=3)
    # the 15px stride survives untouched; only the run's distance from the hall changes (front edge y512 + 15)
    assert [t[1] for t in s.M["torii"]] == pytest.approx([527, 542, 557], abs=0.1)


def test_ward_refuses_a_fence_laid_across_a_standing_torii():
    # the Nagahara case (GM 2026-07-25): the fence is drawn AFTER the temple, so the avenue could not
    # have avoided it - the wall side must catch it, since neither feature can move once drawn
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    # the arch is seated by _avenue_at_threshold at the hall's front edge (y514) + one 20 ft pitch
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 700)], torii_count=1)
    with pytest.raises(ValueError, match=r"the samurai ward fence runs through torii arch\(es\) at \[\(600.0, 520.7\)\]"):
        s.ward("samurai", [(300, 521), (900, 521)], gates=[])


def test_avenue_at_threshold_slides_a_marooned_sando_in_to_its_hall():
    # GM 2026-07-27: "the distance from the front of the temple should be the same as the distance
    # between each torii arch". Tango's Bishamon sando was spaced right at 20 ft and authored 139 ft
    # away, so it read as three red marks beside an unrelated building. The run keeps its direction,
    # its curve and its stride - only its distance from the hall changes.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 700), (600, 710)], torii_count=3)
    ys = [t[1] for t in s.M["torii"]]
    strides = [ys[i + 1] - ys[i] for i in range(2)]
    assert strides == pytest.approx([10, 10], abs=0.1)  # the authored 10px (30 ft) stride is inside the pitch band and stands
    assert ys[0] - (500 + s.px(84) / 2) == pytest.approx(10, abs=0.1)  # ...and the gap to the hall now MATCHES it


def test_avenue_at_threshold_pulls_a_beside_the_hall_gate_onto_the_flank_it_stands_off():
    # a run authored off to the SIDE is measured to the hall's nearest FACE, not its centre (the
    # footprint discipline), so it slides onto the flank it actually stands off rather than diagonally
    # in toward the middle of the building - which is what makes a beside-the-hall gate read as
    # belonging to that hall.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple", torii=[(760, 500)], torii_count=1)
    (tx, ty, _z) = s.M["torii"][0]
    assert ty == 500  # stayed on its own line
    assert tx - (600 + s.px(130) / 2) == pytest.approx(s.px(settlement.TORII_PITCH_FT), abs=0.1)


def test_avenue_at_threshold_leaves_a_degenerate_avenue_alone():
    # nothing to seat, and an arch drawn ON the hall is torii_clear_of_shrine's defect to report -
    # this method translates a sando, it does not paper over a broken one
    s = Settlement(600, 600, seed=1)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    assert s._avenue_at_threshold(300, 300, 40, 30, []) == []
    on_the_hall = [(300.0, 300.0), (300.0, 320.0)]
    assert s._avenue_at_threshold(300, 300, 40, 30, on_the_hall) == on_the_hall


def test_hall_caption_steps_out_of_its_own_sando():
    # GM 2026-07-27: an arch is "never covered by the 'temple of X' label". A hall's caption and its
    # approach both want the ground at the hall's face, so bringing the arches to the threshold put
    # the two on the same spot - the caption takes the hall's other side.
    s = Settlement(1200, 1200, seed=9)
    s.meta(name="T", scale="city", ftpx=3, down_deg=90)
    s.shrine_hall(600, 500, "Temple of Ebisu", w=s.px(130), h=s.px(84), kind="temple", torii=[(600, 700)], torii_count=7, label_below=True)
    cap = [L for L in s.M["labels"] if L[5] == "Temple of Ebisu"][0]
    arches = [(t[0], t[1]) for t in s.M["torii"]]
    txh, tyu, tyd = settlement.torii_halfbox(s.ftpx)
    assert not any(cap[0] < ax + txh and ax - txh < cap[2] and cap[1] < ay + tyd and ay - tyu < cap[3] for ax, ay in arches)
    assert cap[1] > max(ay for _, ay in arches)  # here it stayed on the gen's side, stepping past the far end of the sando


def test_open_seat_answers_where_a_feature_can_actually_stand():
    # GM 2026-07-25: fitting one extra well into a packed quarter cost three regenerate-and-check
    # cycles of hand-picked coordinates because nothing outside the engine could ask _fits where
    # there was room. open_seat asks it directly, so its answer is what placement will actually take.
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="T", scale="town")
    s.block_polys.append([(390, 390), (500, 390), (500, 510), (390, 510)])  # the left half of the rect is no-build
    seat = s.open_seat((400, 400, 600, 500), 20, 20)
    assert seat is not None and s._fits(seat[0], seat[1], 20, 20)  # a seat the real placement path accepts
    assert seat[0] >= 500 and not s._in_blocked(*seat)  # ... off the blocked ground, which a manifest-only scan could not have known

    far = s.open_seat((400, 400, 600, 500), 20, 20, clear_of=[(600, 500)])  # stand away from an existing feature
    assert far is not None and math.hypot(far[0] - 600, far[1] - 500) > math.hypot(seat[0] - 600, seat[1] - 500)

    s.M["commons"] = [{"poly": [(490, 380), (620, 380), (620, 520), (490, 520)]}]  # grazed waste over the clear half
    assert s.open_seat((400, 400, 600, 500), 20, 20, well=True) is None  # a wellhead may not stand in it...
    assert s.open_seat((400, 400, 600, 500), 20, 20) is not None  # ... though anything else may

    s.block_polys.append([(0, 0), (1200, 0), (1200, 1200), (0, 1200)])  # nowhere left at all
    assert s.open_seat((400, 400, 600, 500), 20, 20) is None


def test_draft_byres_scatters_shared_sheds_among_the_houses():
    s, hs = _byre_village()
    placed = s.draft_byres(fraction=0.6, gap=40)  # ~60% of 5 = 3 shared byres
    assert len(placed) == 3 and len(s.M["byres"]) == 3
    assert all(b["w"] > 0 and b["h"] > 0 for b in s.M["byres"])
    assert "<rect" in s.out[-1]  # a byre glyph was drawn


def test_draft_byres_skips_a_homestead_boxed_in_on_all_sides():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 300, "y": 300, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.0}]
    s.placed.append((300, 300, 40, 28))
    for a in range(0, 360, 20):  # wall the homestead in with placed footprints
        rad = math.radians(a)
        s.placed.append((300 + 70 * math.cos(rad), 300 + 70 * math.sin(rad), 60, 60))
    assert s.draft_byres(fraction=1.0) == []  # nowhere to put a byre -> skipped


def test_draft_byres_keeps_off_the_paddy():
    s = _crop_settlement()
    s.M["houses"] = [{"x": 300, "y": 300, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.0}]
    s.placed.append((300, 300, 40, 28))
    s.field_polys.append([(330, 200), (600, 200), (600, 500), (330, 500)])  # paddy on the E half of the ring
    placed = s.draft_byres(fraction=1.0)
    assert len(placed) == 1 and placed[0][0] < 330  # the byre lands on the dry (W) side, off the paddy


def test_draft_byres_uses_the_legacy_size_off_the_to_scale_tiers():
    # a legacy tier (town/city) sizes its byre from the urban glyph grain (bscale), not px(feet) - the
    # non-to-scale branch of the byre sizer.
    s = _town()  # scale="town" -> not to-scale
    hs = [{"x": 300 + i * 170, "y": 350, "w": 40, "h": 28, "kind": "plain", "rot": 0, "wealth": 1.0} for i in range(3)]
    s.M["houses"] = hs
    for h in hs:
        s.placed.append((h["x"], h["y"], h["w"], h["h"]))
    placed = s.draft_byres(fraction=1.0, gap=40)
    assert placed and all(b["w"] > 0 for b in s.M["byres"])


def test_shrine_well_places_a_well_beside_the_hall():
    s = _crop_settlement()
    s.M["religious"] = [{"x": 400, "y": 400, "w": 30, "h": 24, "kind": "shrine"}]
    spot = s.shrine_well(400, 400)
    assert spot is not None
    import math as _m

    assert _m.hypot(spot[0] - 400, spot[1] - 400) <= 115 and len(s.M["wells"]) == 1  # close beside the hall


def test_shrine_well_returns_none_when_boxed_in():
    s = _crop_settlement()
    for a in range(0, 360, 15):  # wall off every ring position around the hall
        rad = math.radians(a)
        for rr in (54, 66, 80, 96, 112):
            s.placed.append((400 + rr * math.cos(rad), 400 + rr * math.sin(rad), 40, 40))
    assert s.shrine_well(400, 400) is None and not s.M["wells"]


def test_a_hall_caption_is_the_same_size_as_a_ministry_caption():
    # GM 2026-08-08: a caption is sized by its GLYPH, not by the institution's rank. A city temple
    # hall and a ministry office are the same size class of building (96-140 ft against 114-140),
    # so their captions match; the temple's greater standing shows in red and bold, not in points.
    s = Settlement(1400, 1400, seed=5)
    s.meta(name="C", scale="city", ftpx=3)
    s.shrine_hall(400, 400, "Temple of Benten", w=s.px(130), h=s.px(84), kind="temple")
    s.ministry(900, 400, "Ministry of Rites")
    temple = next(lb for lb in s.M["labels"] if lb[5] == "Temple of Benten")
    ministry = next(lb for lb in s.M["labels"] if lb[5] == "Ministry of Rites")
    assert _caption_size(temple) == _caption_size(ministry) == settlement.HALL_CAPTION_FS
    # per CHARACTER the two now advance identically - the defect was a temple caption ~44% wider
    # per character than the ministry caption standing 500px away from it
    assert (temple[2] - temple[0]) / len(temple[5]) == pytest.approx((ministry[2] - ministry[0]) / len(ministry[5]), abs=0.01)


# ---- shrine: the primary Shinto hall glyph -------------------------------------------------
def test_shrine_draws_and_records_a_religious_hall():
    s = _village()
    s.shrine(300, 300)
    # TRUE SCALE (2026-07-21): the default is a 62x42 ft tutelary hall drawn through px(), no longer 104x68 raw px
    assert s.M["shrine"] == [300 - s.px(62) / 2, 300 - s.px(42) / 2, s.px(62), s.px(42)]
    assert any(r["kind"] == "shrine" and r["x"] == 300 for r in s.M["religious"])


def test_shrine_hall_guard_refuses_unscaled_pixels_at_coarse_scales():
    # the latent-footgun guard (2026-07-21): four city temples shipped as fixed 100x64 px = 300x192 real ft.
    # At any ftpx > 1, raw-pixel dims implying an impossible hall must raise; s.px(real_ft) passes.
    s = Settlement(2000, 2000, seed=1)
    s.meta(name="G", scale="city", ftpx=3, toscale=True, households=600)
    with pytest.raises(ValueError, match="pass s.px"):
        s.shrine_hall(500, 500, "Temple", w=100, h=64, kind="temple")
    s.shrine_hall(500, 500, "Temple", w=s.px(130), h=s.px(84), kind="temple")
    assert any(r["kind"] == "temple" for r in s.M["religious"])


def test_farm_wells_seats_in_a_dooryard_dodging_crop():
    """The SUCCESS path of the dooryard grid scan (previously covered only incidentally by the city
    regens, which stopped triggering it once Tango's belt got its own seeded wells 2026-07-21): the
    well seats near the steading on clear ground, skipping a crop patch in the scan ring."""
    s = Settlement(1000, 1000, seed=3)
    s.meta(name="Fw2", scale="town", ftpx=1)
    s.M["houses"].append({"x": 500, "y": 500, "w": 44, "h": 29, "rot": 0})
    # the field ENVELOPE blankets every ring spot (well_at refuses inside field_polys), so the ring
    # pass fails; the DRAWN crop covers only the top half, so the fallback - which suspends the
    # envelope and tests the drawn plots - seats the well on the bottom-half rim slack
    s.field_polys.append([(340, 340), (660, 340), (660, 660), (340, 660)])
    s.dry_polys.append([(340, 340), (660, 340), (660, 500), (340, 500)])
    s.M["fields"].append(
        {"name": "f", "kind": "paddy", "outline": [[340, 340], [660, 340], [660, 660], [340, 660]], "plot_polys": [[[600, 600], [648, 600], [648, 648], [600, 648]]]}
    )  # a drawn paddy plot the fallback also dodges
    assert s.farm_wells() == 1
    w = s.M["wells"][0]
    assert w["y"] > 514  # on the rim slack below the drawn crop (+14 margin), never on the crop


def test_farm_wells_drops_a_cluster_with_no_seatable_ground():
    """A steading whose whole reach-disc is blocked ground gets skipped rather than spinning the
    cover loop forever - the well simply cannot seat, and the gate will say so."""
    s = Settlement(1000, 1000, seed=3)
    s.meta(name="Fw", scale="town", ftpx=1)
    s.M["houses"].append({"x": 500, "y": 500, "w": 44, "h": 29, "rot": 0})
    s.block_polys.append([(300, 300), (700, 300), (700, 700), (300, 700)])  # blanket the reach disc
    assert s.farm_wells() == 0
    assert not s.M["wells"]


def test_farm_wells_falls_back_to_envelope_rim_slack():
    """When a steading's whole neighborhood sits inside a field ENVELOPE (the smoothed outline
    claiming more than the crop fills), the primary seating fails and the fallback suspends the
    envelope blocks, seating the well on unplanted rim slack - but never on a DRAWN plot."""
    s = Settlement(1000, 1000, seed=4)
    s.meta(name="Fw2", scale="town", ftpx=1)
    s.M["houses"].append({"x": 500, "y": 500, "w": 44, "h": 29, "rot": 0})
    s.field_polys.append([(200, 200), (800, 200), (800, 800), (200, 800)])  # envelope blankets the disc
    s.M["fields"].append(
        {"name": "t", "kind": "paddy", "outline": [[200, 200], [800, 200], [800, 800], [200, 800]], "bbox": [200, 200, 800, 800], "plot_polys": [[[430, 430], [570, 430], [570, 570], [430, 570]]]}
    )  # drawn crop hugs the house
    assert s.farm_wells() == 1
    wx, wy = s.M["wells"][0]["x"], s.M["wells"][0]["y"]
    assert not (430 <= wx <= 570 and 430 <= wy <= 570)  # seated on rim slack, not on the crop


def test_open_seat_refuses_a_seat_whose_FOOTPRINT_crosses_the_bound():
    """The martial-hall bug, as a unit test (GM 2026-07-25). s.bound is the ring-road loop a city
    packs inside, and `_fits` tests only a candidate's CENTER against it - so open_seat handed back
    a compound seat whose SE corner lay across Tango's patrol bed. open_seat now tests the whole
    footprint against the bound (and ONLY the bound: block polys and corridors are soft
    reservations a footprint may legitimately overhang, and tightening those cost two pool maps a
    feature apiece when it was tried)."""
    s = Settlement(1200, 1200, seed=3)
    s.meta(name="C", scale="city", ftpx=3)
    s.bound = [[100, 100], [700, 100], [700, 700], [100, 700]]
    over = (665, 300, 695, 320)  # every candidate here keeps its CENTER inside x=700 but its right edge past it
    assert s.open_seat(over, 80, 20) is None
    assert s.open_seat(over, 80, 20, footprint=False) is not None  # the old center-only behavior
    assert s.open_seat((300, 300, 400, 320), 80, 20) is not None  # well inside the bound: fine


def test_well_ground_clear_refuses_water_and_crop():
    """You do not sink a well in a watercourse, and you do not sink one in a crop plot. Placement
    predicted everything else about a well site - lanes, compounds, the bound, its neighbors - but
    never the water or the crop, which is how the overlap matrix found four wells standing in
    ditches, a channel and a hatake plot across three maps."""
    s = _town()
    assert s._well_ground_clear(500, 500)  # bare ground
    s.M["streams"] = [{"poly": [[500, 300], [500, 700]], "w": 9}]
    assert not s._well_ground_clear(500, 500)
    assert s._well_ground_clear(900, 500)  # well clear of it
    s.M["streams"] = []
    s.M["field_ditches"] = [{"poly": [[400, 500], [600, 500]], "w": 1.5}]
    assert not s._well_ground_clear(500, 500)
    s.M["field_ditches"] = []
    s.M["pond"] = [500, 500, 40, 24]
    assert not s._well_ground_clear(505, 500)
    assert s._well_ground_clear(900, 900)
    s.M["pond"] = None
    s.M["dry_plots"] = [{"poly": [[480, 480], [560, 480], [560, 560], [480, 560]], "crop": "barley", "theta": 0}]
    assert not s._well_ground_clear(520, 520)  # inside the plot
    assert not s._well_ground_clear(474, 520)  # its drawn head laps the plot's edge
    assert s._well_ground_clear(900, 900)


def test_place_wells_cistern_kind_is_recorded():
    """kind='cistern' marks a josui-ido on the buried main (research 021 item 4) - the record
    carries the kind so the service-band check and the samurai-quarter exemption can read it."""
    s = Settlement(600, 600, seed=5)
    seats = s.place_wells((100, 100, 300, 300), spacing=80, kind="cistern", coverage=False)
    assert seats, "the open ground must seat at least one well"
    ws = [w for w in s.M["wells"] if isinstance(w, dict) and w.get("kind") == "cistern"]
    assert len(ws) == len(seats)


def test_open_seat_disc_uses_the_true_radius_of_a_round_candidate():
    """A wellhead is a DISC, so its reach is its radius - not the half-diagonal of the probe box
    around it, which is the documented over-restriction in this skill's CLAUDE.md. Exact rather
    than a relaxation, and opt-in: the derived well grid leans on the conservative radius as its
    padding, and making it exact there put a wellhead on a building."""

    def seat(disc):
        s = settlement.Settlement(600, 600, seed=9)
        s.meta(scale="city", ftpx=3)
        s.placed.append((300.0, 300.0, 40.0, 40.0))  # one standing footprint in the middle
        return s.open_seat((296, 330, 340, 372), 16, 16, step=2.0, footprint=False, disc=disc)

    loose, exact = seat(False), seat(True)
    assert exact is not None, "the exact disc reach must find the gap the half-diagonal refuses"
    assert loose is None or math.hypot(exact[0] - 300, exact[1] - 300) <= math.hypot(loose[0] - 300, loose[1] - 300)
