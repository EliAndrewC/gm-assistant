"""Gate checks for field cover, cremation, streams and field ditches (test_segments_05_fields_and_funerary split by feature 122; tests verbatim)."""

from tests.check_village._builders import (
    _FORK_MAINS,
    _MON,
    _SHR,
    _city_dead,
    _cross_M,
    _dead,
    _dryplot,
    _farmhouse,
    _field,
    _nuc_grid,
    _nuc_village_M,
    _nuc_with_windbreak,
    _supply_M,
    _tips_M,
    f,
)


# ---- field_ditches_reach_source_and_sink (role-aware: supply->source, drain->sink) ----------
def test_field_ditches_reach_source_and_sink_fires_when_ungrounded():
    # a supply ditch with no pond source AND a drain with no runoff sink - both dangle (the failure
    # path of the role-aware grounding). The GOOD case is covered by the real maps (kikuta passes with
    # its full pond->canal->cascade->drain->off-map network; the wip Hoshigaoka likewise).
    M = {"field_ditches": [{"poly": [[300, 300], [500, 300]], "role": "main", "field": "f"}, {"poly": [[300, 600], [500, 600]], "role": "drain", "field": "f"}]}
    assert "field_ditches_reach_source_and_sink" in f(M)


def test_structures_clear_of_dry_plots_fires_when_a_farmstead_stands_on_a_hem_strip():
    # GM 2026-07: farmsteads (house + threshing yard) stood on Tango's fn1/nw1 dry hems - the
    # plots were guarded center-only, so a footprint could overlap a strip edge
    M = {"dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "barley", "theta": 0.5}], "houses": [{"x": 480, "y": 372, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "structures_clear_of_dry_plots" in f(M)


def test_structures_clear_of_dry_plots_passes_when_the_farmstead_abuts_the_strip():
    # abutting is fine (a hem may run right up to a wall) - only real overlap fires
    M = {"dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "barley", "theta": 0.5}], "houses": [{"x": 400, "y": 396, "w": 46, "h": 28, "rot": 0, "kind": "plain"}]}
    assert "structures_clear_of_dry_plots" not in f(M)


def test_groves_clear_of_dry_plots_fires_when_a_clump_stands_in_the_crop():
    M = {
        "dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "soy", "theta": 1.2}],
        "village_groves": [{"role": "belt", "r": 11, "clumps": [[400, 340]], "poly": [[380, 320], [420, 320], [420, 360], [380, 360]]}],
    }
    assert "groves_clear_of_dry_plots" in f(M)


def test_groves_clear_of_dry_plots_passes_when_the_belt_hugs_the_edge():
    M = {
        "dry_plots": [{"poly": [[300, 300], [500, 300], [500, 380], [300, 380]], "crop": "soy", "theta": 1.2}],
        "village_groves": [{"role": "belt", "r": 11, "clumps": [[400, 396]], "poly": [[380, 384], [420, 384], [420, 408], [380, 408]]}],
    }
    assert "groves_clear_of_dry_plots" not in f(M)


def test_field_ditches_ground_via_the_moat():
    # a MOATED city's combs ground at the moat both ways: the supply taps it (frm=moat is a SOURCE -
    # it is a fed watercourse, per city_moat_irrigates_fields) and a collector may empty into it
    # (to=moat is a SINK - the moat is the city's storm drain). Added for Tango's comb-field port.
    M = {
        "field_ditches": [{"poly": [[300, 300], [500, 300]], "role": "main", "field": "f"}, {"poly": [[300, 600], [500, 600]], "role": "drain", "field": "f"}],
        "channels": [
            {"poly": [[290, 296], [304, 308]], "frm": {"kind": "moat"}, "to": {"kind": "field", "name": "f"}, "w": 2.5},
            {"poly": [[494, 596], [520, 612]], "frm": {"kind": "drain"}, "to": {"kind": "moat"}, "w": 2.5},
        ],
    }
    assert "field_ditches_reach_source_and_sink" not in f(M)


def test_delivery_ditches_taper_fires_on_a_blunt_ditch():
    # a delivery ditch (role "branch") ending at nearly full width - it should have shed its water
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f", "w": 4.0, "w_tail": 4.0}]}
    assert "delivery_ditches_taper" in f(M)


def test_delivery_ditches_taper_passes_when_it_narrows():
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f", "w": 4.0, "w_tail": 1.5}]}
    assert "delivery_ditches_taper" not in f(M)


def test_delivery_ditches_taper_exempts_ditches_without_recorded_widths():
    # the older water_field engine records no head/tail width - nothing to judge, so it is skipped
    M = {"field_ditches": [{"poly": [[300, 300], [500, 500]], "role": "branch", "field": "f"}]}
    assert "delivery_ditches_taper" not in f(M)


def test_channels_join_not_cross_at_fork_fires_on_a_delivery_at_the_division():
    # a delivery (role "branch") taking off AT the fork - the 4-way star that reads as a crossroads
    M = {"field_ditches": _FORK_MAINS + [{"poly": [[100, 100], [140, 140]], "role": "branch", "field": "f", "w": 2.7, "w_tail": 1.0}]}
    assert "channels_join_not_cross_at_fork" in f(M)


def test_channels_join_not_cross_at_fork_passes_when_the_delivery_is_downstream():
    # the delivery branches off a supply canal 50px downstream of the fork - a clean offtake
    M = {"field_ditches": _FORK_MAINS + [{"poly": [[150, 100], [150, 145]], "role": "branch", "field": "f", "w": 2.7, "w_tail": 1.0}]}
    assert "channels_join_not_cross_at_fork" not in f(M)


def test_dry_plot_furrows_vary_fires_when_two_neighbours_share_an_angle():
    # 4 dry plots in a row; the first two are edge-adjacent AND run their furrows the same way -> fires
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.2), _dryplot(380, 0.9), _dryplot(420, 0.4)]
    assert "dry_plot_furrows_vary" in f({"dry_plots": dp})


def test_dry_plot_furrows_vary_passes_when_neighbours_differ():
    # adjacent plots alternate orientation, so no neighboring pair shares a row direction
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.9), _dryplot(380, 0.2), _dryplot(420, 0.9)]
    assert "dry_plot_furrows_vary" not in f({"dry_plots": dp})


def test_dry_plot_furrows_vary_skipped_for_a_contour_village():
    # a STEEP / terraced village declares contour furrows (meta.dry_furrows_vary=False) - the rows converge on
    # the contour for erosion control, so identical adjacent angles are CORRECT and the check does not fire
    dp = [_dryplot(300, 0.2), _dryplot(340, 0.2), _dryplot(380, 0.2), _dryplot(420, 0.2)]  # all aligned
    assert "dry_plot_furrows_vary" not in f({"meta": {"dry_furrows_vary": False}, "dry_plots": dp})


# ---- dry_plot_seams_shared (hem seams are single straight lines both quads lie on) -----------
def test_dry_plot_seams_shared_fires_on_a_lap():
    # the concave-bend failure: the second column's quad laps 2 px into its neighbor
    a = {"poly": [[300, 300], [346, 300], [346, 336], [300, 336]], "theta": 0.2}
    b = {"poly": [[344, 300], [390, 302], [390, 338], [344, 336]], "theta": 0.9}
    assert "dry_plot_seams_shared" in f({"dry_plots": [a, b]})


def test_dry_plot_seams_shared_fires_on_a_gap_wedge():
    # the convex-bend failure: both columns share the base corner at (346,300) but the second's
    # side edge tilts 6 px off the first's over its depth - a bare wedge opens between them
    a = {"poly": [[300, 300], [346, 300], [346, 380], [300, 380]], "theta": 0.2}
    b = {"poly": [[346, 300], [392, 300], [398, 380], [352, 380]], "theta": 0.9}
    assert "dry_plot_seams_shared" in f({"dry_plots": [a, b]})


def test_dry_plot_seams_shared_passes_a_shared_seam_with_a_depth_step():
    # clean abutment: one straight seam at x=346, the second column shallower - the ragged outer
    # edge steps ALONG the shared line, which is exactly the raggedness the generator intends
    a = {"poly": [[300, 300], [346, 300], [346, 380], [300, 380]], "theta": 0.2}
    b = {"poly": [[346, 300], [392, 300], [392, 350], [346, 350]], "theta": 0.9}
    assert "dry_plot_seams_shared" not in f({"dry_plots": [a, b]})


def test_dry_plot_seams_shared_skips_singletons_and_separated_plots():
    # one plot has no seams; two plots a field apart never meet (the bbox prefilter path)
    a = {"poly": [[300, 300], [346, 300], [346, 380], [300, 380]], "theta": 0.2}
    c = {"poly": [[900, 300], [946, 300], [946, 380], [900, 380]], "theta": 0.9}
    assert "dry_plot_seams_shared" not in f({"dry_plots": [a]})
    assert "dry_plot_seams_shared" not in f({"dry_plots": [a, c]})


def test_channel_source_anchored_fires_on_bad_anchor():
    M = {"channels": [{"poly": [[100, 100], [110, 120], [120, 140]], "frm": {"kind": "bogus"}, "to": {"kind": "offmap"}}]}
    assert "channel_source_anchored[0]" in f(M)


def test_field_supply_visibly_sourced_fires_on_a_dangling_comb_origin():
    # origin (450,250): 150px from the stream, far from every view edge; the only drawn stroke
    # is nowhere near the origin, so it cannot rescue it
    assert "field_supply_visibly_sourced[x]" in f(_supply_M([450, 250], drawn_channels=[{"pts": [[900, 900], [950, 950]]}]))


def test_field_supply_visibly_sourced_passes_on_a_moat_bank():
    # a comb origin on the moat bed is sourced (the moat-fed city-comb pattern)
    M = _supply_M([450, 110])
    M["streams"] = []
    M["moat"] = [[100, 100], [800, 100], [800, 105]]
    M["moat_width"] = 26
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_passes_on_a_pond_rim():
    # a comb origin inside/on the pond ellipse is sourced (Tango's in-wall nw1 comb)
    M = _supply_M([450, 250])
    M["pond"] = [455, 255, 30, 20]
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_ditch_tips_land_on_the_trunk_fires_on_a_tip_past_the_canal():
    # both tips 6px BEYOND the trunk centerline: inside near_any's 13px net (so field_ditches_terminate
    # is happy) but 3.5px outside the trunk's drawn band, so a stub shows through
    assert "field_ditch_tips_land_on_the_trunk" in f(_tips_M([[100, 256], [100, 94]]))


def test_field_ditch_tips_land_on_the_trunk_passes_on_a_tip_in_the_band():
    # tips 1px off the centerline - buried under the trunks' own strokes, a clean T at each end
    assert "field_ditch_tips_land_on_the_trunk" not in f(_tips_M([[100, 249], [100, 101]]))


def test_water_channels_join_not_cross_fires_on_a_stub_through_the_trunk():
    # the vertical stroke crosses the trunk and stops 6px past it; the trunk's own nearest end is
    # 100px away, so NEITHER tip is buried in the other's band -> it reads as a 4-way intersection.
    # The third stroke is far off in the corner (the bbox-reject path).
    M = _cross_M(
        {"pts": [[0, 100], [200, 100]], "w0": 5, "w1": 5},
        {"pts": [[100, 150], [100, 94]], "w0": 3, "w1": 3},
        {"pts": [[380, 380], [390, 390]], "w0": 3, "w1": 3},
    )
    assert "water_channels_join_not_cross" in f(M)


def test_water_channels_join_not_cross_passes_on_a_shallow_offtake():
    # a delivery taking off at a shallow angle overruns the crossing along its OWN line by ~40px,
    # yet its tip stays 1px off the trunk centerline - under the ink, a clean Y. The second pair
    # (widths defaulted, bboxes overlapping but never crossing) exercises the no-crossing path.
    M = _cross_M(
        {"pts": [[0, 100], [200, 100]], "w0": 5, "w1": 5},
        {"pts": [[150, 140], [50, 99]], "w0": 3, "w1": 3},
        {"pts": [[10, 200], [190, 200]]},
    )
    assert "water_channels_join_not_cross" not in f(M)


def test_field_supply_visibly_sourced_passes_on_a_river_bank():
    # a comb origin sitting directly on a RIVER bed is sourced (Nagahara's far-bank fan pattern)
    M = _supply_M([450, 110])
    M["streams"] = []
    M["river"] = {"pts": [[100, 100], [800, 100]], "w": 40}
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_passes_on_a_cargo_canal():
    # a comb origin on a cargo-canal bank is sourced (a Lion-lands water-town form)
    M = _supply_M([450, 104])
    M["streams"] = []
    M["canals"] = [{"poly": [[100, 100], [800, 100]], "w": 12}]
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_passes_on_a_cascade_ditch():
    # tail-water reuse: the origin sits on ANOTHER comb's ditch (the standard way a city's
    # drainage waters the fields below it - Hirameki's e2 pattern)
    M = _supply_M([450, 250])
    M["field_ditches"].append({"poly": [[300, 248], [600, 252]], "role": "drain", "field": "other", "w": 4})
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_skips_a_field_with_no_mains():
    # no main ditches recorded for the fed field -> nothing visible starts anywhere; not this check's call
    M = _supply_M([450, 250])
    M["field_ditches"] = []
    assert not any(c.startswith("field_supply_visibly_sourced") for c in f(M))


def test_field_supply_visibly_sourced_passes_with_a_drawn_tap():
    # a drawn tap stroke joins the origin to the stream bed - the visual chain is complete
    M = _supply_M([450, 250], drawn_channels=[{"pts": [[450, 104], [450, 250]]}])
    assert "field_supply_visibly_sourced[x]" not in f(M)


def test_field_supply_visibly_sourced_ignores_the_combs_own_canal():
    # the only drawn stroke at the origin is the comb's own main heading INTO the field - it
    # carries water downstream, not from a source, so the origin still dangles
    M = _supply_M([450, 250], drawn_channels=[{"pts": [[450, 250], [450, 320], [460, 400]]}])
    assert "field_supply_visibly_sourced[x]" in f(M)


def test_field_supply_visibly_sourced_passes_at_the_view_edge():
    # an origin at the map edge is presumed to continue off-map (the fn1/fn2 pattern)
    assert "field_supply_visibly_sourced[x]" not in f(_supply_M([450, 20]))


def test_field_supply_visibly_sourced_skips_a_drawn_supply_channel():
    # a DRAWN supply channel carries its own visual continuity (its ends are anchor-checked)
    assert "field_supply_visibly_sourced[x]" not in f(_supply_M([450, 250], drawn=True))


def test_streams_avoid_fields_fires():
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[200, 200], [200, 500]]}]}  # first point sits inside the field
    assert "streams_avoid_fields" in f(M)


def test_streams_avoid_fields_allows_a_drain_fed_brook():
    # a brook anchored to the field's DRAIN starts at the outfall (inside the envelope) and runs off-map - legit
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[300, 380], [300, 550], [300, 700]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}}]}
    assert "streams_avoid_fields" not in f(M)


def test_streams_avoid_fields_still_fires_when_a_drain_brook_reenters_the_field():
    # a drain-fed brook that leaves then CUTS BACK across the crop is still a defect
    M = {"fields": [_field("f", 100, 100, 400, 400)], "streams": [{"poly": [[300, 380], [300, 600], [250, 250]], "frm": {"kind": "drain"}, "to": {"kind": "offmap"}}]}  # last leg re-enters the field
    assert "streams_avoid_fields" in f(M)


def test_streams_avoid_fields_allows_a_stream_that_ends_at_the_field():
    # a stream anchored INTO the field (to=field) ends inside it - the connection is legitimate
    M = {
        "fields": [_field("f", 100, 100, 400, 400)],
        "streams": [{"poly": [[300, 700], [300, 500], [300, 300]], "frm": {"kind": "offmap"}, "to": {"kind": "field", "name": "f"}}],
    }  # ends inside the field
    assert "streams_avoid_fields" not in f(M)


def test_fields_clear_of_road_fires():
    M = {"fields": [_field("f", 100, 100, 400, 400)], "road": [[50, 250], [500, 250]], "road_width": 26}
    assert "fields_clear_of_road" in f(M)


def test_commons_clear_of_paddies_fires_when_scrub_sits_in_a_field():
    # The check tests the DRAWN OUTCOME, not the patch's bbox CENTER (the scatter skips every paddy point by
    # construction, so a center-over-water test was only a proxy). It fires when a patch can clothe NOTHING:
    M = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    M["commons"] = [{"x": 600, "y": 600, "w": 60, "h": 60, "rot": 0, "poly": [[570, 570], [630, 570], [630, 630], [570, 630]]}]  # wholly inside the paddy -> draws nothing
    assert "commons_clear_of_paddies" in f(M)
    # ...but an INTERIOR FILL - the patch that clothes the voids an irregular field leaves inside its own bbox -
    # legitimately has its CENTER on the crop while every glyph it draws lands in the open ground around it.
    # Scoring the center failed this correct patch, which is why the rule changed (GM, 2026-07: Akagahara's fan
    # void rendered as bare clay because nothing was allowed to cover it).
    fill = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    fill["commons"] = [{"x": 600, "y": 600, "w": 400, "h": 400, "rot": 0, "poly": [[400, 400], [800, 400], [800, 800], [400, 800]]}]
    assert "commons_clear_of_paddies" not in f(fill)
    # a patch with no recorded polygon is skipped rather than crashing
    nopoly = _nuc_village_M(_nuc_grid(), fields=[_field("p", 540, 540, 700, 700)])
    nopoly["commons"] = [{"x": 600, "y": 600, "w": 60, "h": 60, "rot": 0}]
    assert "commons_clear_of_paddies" not in f(nopoly)


def test_commons_beyond_the_windbreak_fires_when_between_grove_and_village():
    houses, ccx, ccy, M = _nuc_with_windbreak()
    M["commons"] = [{"x": ccx - 70, "y": ccy - 70, "w": 80, "h": 200, "rot": 0}]  # NOT past the grove
    assert "commons_beyond_the_windbreak" in f(M)


def test_commons_beyond_the_windbreak_passes_when_past_the_grove():
    houses, ccx, ccy, M = _nuc_with_windbreak()
    M["commons"] = [{"x": ccx - 280, "y": ccy - 280, "w": 80, "h": 200, "rot": 0}]  # well beyond the belt
    assert "commons_beyond_the_windbreak" not in f(M)


def test_commons_beyond_the_windbreak_exempts_general_hinterland_land():
    # the general marginal hill land types - 'grazing' scrub, open 'pasture', coppice 'woodland' - are the
    # hinterland catena (any dry flank), NOT the windward fuel commons, so each is exempt even when NOT beyond
    # the windbreak; only the default fuel/fodder commons follows the toposequence rule.
    for role in ("grazing", "pasture", "woodland"):
        houses, ccx, ccy, M = _nuc_with_windbreak()
        M["commons"] = [{"x": ccx - 70, "y": ccy - 70, "w": 80, "h": 200, "rot": 0, "role": role}]
        assert "commons_beyond_the_windbreak" not in f(M)


def test_commons_beyond_check_skipped_without_a_windbreak():
    # nucleated + commons but NO windbreak grove -> the beyond-the-windbreak check cannot run (wbs empty)
    M = _nuc_village_M(_nuc_grid())
    M["commons"] = [{"x": 100, "y": 100, "w": 60, "h": 60, "rot": 0}]
    assert "commons_beyond_the_windbreak" not in f(M)


def test_woodland_clear_of_crops_fires_on_overlap_and_shade_passes_when_set_back_north():
    # a managed-woodland patch must NOT overlap a crop NOR shade it from the sunny SOUTH side (trees cast
    # shadows north, maps are north-up); a patch set back to the NORTH is fine. Covers paddy + dry_plots.
    p = _field("p", 400, 400, 700, 600)
    base = {"meta": {"scale": "village"}, "fields": [p]}

    def wood(poly):
        cx = sum(v[0] for v in poly) / len(poly)
        cy = sum(v[1] for v in poly) / len(poly)
        return {"x": cx, "y": cy, "w": 100, "h": 100, "rot": 0, "role": "woodland", "poly": poly}

    over = {**base, "commons": [wood([[500, 450], [600, 450], [600, 550], [500, 550]])]}  # sits ON the paddy
    assert "woodland_clear_of_crops" in f(over)
    shade = {**base, "commons": [wood([[500, 612], [640, 612], [640, 660], [500, 660]])]}  # just SOUTH -> shades it
    assert "woodland_clear_of_crops" in f(shade)
    ok = {**base, "commons": [wood([[500, 300], [640, 300], [640, 344], [500, 344]])]}  # well NORTH -> clear
    assert "woodland_clear_of_crops" not in f(ok)
    dry = {
        **base,
        "dry_plots": [{"poly": [[800, 400], [900, 400], [900, 500], [800, 500]], "crop": "soy", "theta": 0.0}],
        "commons": [wood([[840, 420], [940, 420], [940, 520], [840, 520]])],
    }  # overlaps a DRY plot
    assert "woodland_clear_of_crops" in f(dry)


def test_woodland_clear_of_grove_fires_when_on_the_fengshui_grove():
    # a coppice woodland patch and the protected fengshui grove are DISTINCT woods - a patch sitting on a grove
    # clump fires; one on its own ground does not.
    p = _field("p", 400, 400, 700, 600)
    patch = {"x": 200, "y": 200, "w": 100, "h": 100, "rot": 0, "role": "woodland", "poly": [[150, 150], [250, 150], [250, 250], [150, 250]]}
    base = {"meta": {"scale": "village"}, "fields": [p], "commons": [patch]}
    on = {**base, "village_groves": [{"role": "windbreak", "x": 200, "y": 200, "r": 14, "clumps": [[200, 200]]}]}  # clump inside the patch
    assert "woodland_clear_of_grove" in f(on)
    off = {**base, "village_groves": [{"role": "windbreak", "x": 900, "y": 900, "r": 14, "clumps": [[900, 900]]}]}  # grove far away
    assert "woodland_clear_of_grove" not in f(off)


def test_farmhouse_sizes_vary_fires_when_flat():
    M = {"meta": {"scale": "village"}, "houses": [_farmhouse(300 + 60 * i, 300) for i in range(12)]}
    assert "farmhouse_sizes_vary" in f(M)  # _farmhouse has no wealth -> all at the baseline tier


def test_farmhouse_sizes_vary_passes_with_a_spread():
    houses = []
    for i in range(12):
        h = _farmhouse(300 + 60 * i, 300)
        h["wealth"] = 0.9 if i % 3 == 0 else (1.12 if i % 3 == 1 else 1.0)
        houses.append(h)
    assert "farmhouse_sizes_vary" not in f({"meta": {"scale": "village"}, "houses": houses})


# --- labels_render_on_top (label text is never covered) ---
def test_labels_render_on_top_fires_when_a_kido_covers_a_label():
    M = {"labels": [[100, 100, 300, 120, 5, "Ministry of Retainers"]], "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_fires_when_a_gate_structure_covers_a_label():
    M = {"labels": [[150, 100, 250, 120, 5, "gate label"]], "gate_structs": [{"x": 200, "y": 110, "w": 100, "h": 40, "z": 1000}]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_fires_when_a_torii_covers_a_label():
    M = {"labels": [[185, 95, 215, 120, 5, "shrine"]], "torii": [[200, 110, 1000]]}
    assert "labels_render_on_top" in f(M)


def test_labels_render_on_top_passes_when_the_label_is_above():
    # same overlap, but the label's draw-z is higher than the structure's - it renders on top, readable
    M = {"labels": [[100, 100, 300, 120, 9999, "Ministry of Retainers"]], "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}]}
    assert "labels_render_on_top" not in f(M)


def test_labels_render_on_top_handles_a_textless_label():
    M = {
        "labels": [[150, 100, 250, 120, 5]],  # a field label recorded without text
        "kido": [{"x": 200, "y": 110, "z": 1000, "bbox": [150, 90, 250, 130]}],
    }
    assert "labels_render_on_top" in f(M)


def test_funerary_clear_of_fields_fires_when_a_cremation_ground_sits_on_a_field():
    # GM 2026-07 (Nagahara): a cremation ground on the far-bank comb's crop + ditch
    field = [{"name": "fe1", "kind": "paddy", "outline": [[300, 300], [700, 300], [700, 700], [300, 700]], "bbox": [300, 300, 700, 700]}]
    fire = {"fields": field, "cremation_grounds": [{"x": 500, "y": 500, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_clear_of_fields" in f(fire)
    ok = {"fields": field, "cremation_grounds": [{"x": 500, "y": 850, "w": 116, "h": 80, "rot": 0}]}
    assert "funerary_clear_of_fields" not in f(ok)


def test_settlement_has_cemetery_fires_when_missing():
    assert "settlement_has_cemetery" in f(_dead("village", []))


def test_settlement_has_cemetery_exempts_hamlet():
    assert "settlement_has_cemetery" not in f(_dead("hamlet", []))


def test_settlement_has_cemetery_passes_when_present():
    assert "settlement_has_cemetery" not in f(_dead("village", [{"x": 300, "y": 300, "w": 80, "h": 56, "rot": 0}]))


def test_cemetery_clear_of_shrine_fires_when_on_the_hall():
    # graves fill the shrine's YARD but never sit ON the sacred hall itself (this grave overlaps it)
    assert "cemetery_clear_of_shrine" in f(_dead("village", [{"x": 540, "y": 520, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_cemetery_clear_of_shrine_passes_when_off_the_hall():
    assert "cemetery_clear_of_shrine" not in f(_dead("village", [{"x": 900, "y": 900, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_cemetery_clear_of_shrine_allows_a_grave_in_the_precinct():
    # NEW (L7R): the shrine is Shinseist and its monk tends the dead, so a grave NEAR the shrine (in the yard,
    # off the hall) is FINE - the old kegare-distance rule is gone; only the sacred hall + torii stay clear
    M = {
        "meta": {"scale": "village"},
        "cemeteries": [{"x": 615, "y": 500, "w": 80, "h": 56, "rot": 0}],
        "religious": _SHR,
    }  # 115px from the shrine center (old rule would fire) but clear of the hall's east edge
    assert "cemetery_clear_of_shrine" not in f(M)


def test_cemetery_clear_of_shrine_fires_on_a_grave_under_the_torii():
    # the sacred GATEWAY stays clear too - a grave on the torii arch fires (hall placed far off, so it is the torii)
    M = {
        "meta": {"scale": "village"},
        "cemeteries": [{"x": 500, "y": 504, "w": 60, "h": 40, "rot": 0}],
        "religious": [{"kind": "shrine", "x": 500, "y": 760, "w": 30, "h": 24}],
        "torii": [[500, 500, 1]],
    }
    assert "cemetery_clear_of_shrine" in f(M)


def test_village_graveyard_by_shrine_fires_when_set_apart():
    # L7R: the village shrine's monk performs the funerary rites, so the graveyard sits in its precinct
    assert "village_graveyard_by_shrine" in f(_dead("village", [{"x": 1200, "y": 1200, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_village_graveyard_by_shrine_passes_when_in_precinct():
    assert "village_graveyard_by_shrine" not in f(_dead("village", [{"x": 640, "y": 500, "w": 80, "h": 56, "rot": 0}], religious=_SHR))


def test_village_graveyard_by_shrine_exempts_a_hilltop_shrine():
    # a hilltop shrine is exempt (graves do not climb the sacred hill); with no flat shrine the ground is by-eye
    M = _dead("village", [{"x": 1200, "y": 1200, "w": 80, "h": 56, "rot": 0}], religious=[{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}])
    M["hill"] = [500, 500, 200, 150]
    assert "village_graveyard_by_shrine" not in f(M)


def test_cemetery_in_temple_precinct_fires_when_far_from_hall():
    assert "cemetery_in_temple_precinct" in f(_dead("town", [{"x": 1500, "y": 1500, "w": 80, "h": 56, "rot": 0}], religious=_MON))


def test_cemetery_in_temple_precinct_passes_when_by_hall():
    assert "cemetery_in_temple_precinct" not in f(_dead("town", [{"x": 560, "y": 520, "w": 80, "h": 56, "rot": 0}], religious=_MON))


def test_cemetery_clear_of_shrine_fires_on_a_mausoleum_on_the_hall():
    # the off-the-hall rule covers MAUSOLEA too, not just graveyards (this one overlaps the shrine hall)
    M = {"meta": {"scale": "village"}, "mausoleums": [{"x": 540, "y": 520, "w": 74, "h": 58, "rot": 0}], "religious": [{"kind": "shrine", "x": 500, "y": 500, "w": 100, "h": 68}]}
    assert "cemetery_clear_of_shrine" in f(M)


def test_city_graveyard_count_fires_when_too_few():
    assert "city_graveyard_count" in f(_city_dead(cems=[(300, 300)]))


def test_city_graveyard_count_fires_when_too_many():
    assert "city_graveyard_count" in f(_city_dead(cems=[(300, 300), (350, 300), (400, 300), (700, 300), (100, 100)]))


def test_city_graveyard_count_passes_at_three():
    assert "city_graveyard_count" not in f(_city_dead())


def test_walled_graveyards_inside_and_outside_fires_when_all_inside():
    assert "walled_graveyards_inside_and_outside" in f(_city_dead(cems=[(300, 300), (700, 300)]))
